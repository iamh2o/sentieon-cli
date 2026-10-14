"""Contracts for the explicit experimental Ultima+ONT profile.

Synthetic headers/models only. These cases do not establish scientific
accuracy or compatibility of the proprietary joint calling model with Ultima.
"""

import argparse
import hashlib
import json
import logging
from pathlib import Path
from types import SimpleNamespace

import pytest

from sentieon_cli import ultima_pangenome as up
from sentieon_cli.hybrid_pangenome import HybridPangenome
from sentieon_cli.pipeline import DagExecutionError
from sentieon_cli.pangenome_meta import HaplHeader, PangenomeReference


def header(rg_id="ug", sample="donor", platform="ULTIMA", length=1000):
    return (
        "@HD\tVN:1.6\tSO:coordinate\n"
        f"@SQ\tSN:chr1\tLN:{length}\n"
        f"@RG\tID:{rg_id}\tSM:{sample}\tPL:{platform}\n"
        "@PG\tID:dedup\tPN:sentieon\tCL:sentieon driver --algo Dedup\n"
    )


@pytest.fixture
def candidate(tmp_path):
    p = HybridPangenome()
    p.setup_logging(argparse.Namespace(loglevel="WARNING"))
    p.experimental_ultima = True
    p.output_vcf = tmp_path / "sample.vcf.gz"
    p.reference = tmp_path / "reference.fa"
    p.gbz = tmp_path / up.GRAPH
    p.hapl = tmp_path / up.HAPLOTYPES
    p.pop_vcf = tmp_path / "population.vcf.gz"
    p.model_bundle = tmp_path / "joint.bundle"
    p.sr_model_bundle = tmp_path / "ultima.bundle"
    p.sr_aln = [tmp_path / "ug.bam"]
    p.lr_aln = [tmp_path / "ont.bam"]
    for path in [p.reference, p.gbz, p.hapl, p.pop_vcf, p.model_bundle,
                 p.sr_model_bundle, *p.sr_aln, *p.lr_aln]:
        path.write_bytes(b"synthetic fixture")
    Path(str(p.reference) + ".fai").write_text("chr1\t1000\t0\t80\t81\n")
    for path in p.sr_aln + p.lr_aln:
        Path(str(path) + ".bai").write_bytes(b"index fixture")
    Path(str(p.pop_vcf) + ".tbi").write_bytes(b"index fixture")
    p.fai_data = {"chr1": {"length": 1000}}
    p.sr_readgroups = [[{"ID": "ug", "SM": "donor", "PL": "ULTIMA"}]]
    p.lr_readgroups = [[{"ID": "ont", "SM": "donor", "PL": "ONT"}]]
    p.sample_sm = "donor"
    p.reference_build = "hg38"
    p.pangenome_ref_name = "GRCh38"
    p.pangenome_contig_prefix = "GRCh38#0#"
    p.dry_run = True
    p.cores = 4
    p.tmp_dir = tmp_path / "work"
    p.tmp_dir.mkdir()
    p.shards = []
    p.pop_vcf_contigs = {"chr1": 1000}
    p.pop_vcf_header = [
        "##fileformat=VCFv4.2",
        f"##SentieonVcfID={up.POPULATION_ID}",
        "##contig=<ID=chr1,length=1000>",
    ]
    profile = up.UltimaProfile(p)
    p.ultima_profile = profile
    profile.start()
    yield p, profile
    logging.getLogger("sentieon_cli").removeHandler(profile.messages)


def jobs(dag):
    return {job.name: job for job in [*dag.ready_jobs, *dag.waiting_jobs]}


def test_routing_channels_filters_tags_and_index_dependencies(candidate):
    p, profile = candidate
    dag = p.build_dag()
    graph = jobs(dag)
    lift = str(graph["mm2-lift"].shell)
    assert str(p.sr_model_bundle / "minimap2.model") in lift
    assert str(p.model_bundle / "minimap2.model") not in lift
    assert "-y" in lift and "LR:2" in lift and "--secondary=yes" not in lift
    extraction = str(graph["extract-kmc"].shell)
    assert str(p.model_bundle / "extract.model") in extraction
    assert "tp,t0" in extraction and "0xf00:0" in extraction
    assert str(p.lr_aln[0]) in extraction and "samtools fasta" in extraction
    for name in ("dnascope", "pangenome-sv"):
        call = str(graph[name].shell)
        assert "UltimaReadFilter,rgid=ug" in call
        assert "UltimaReadFilter,rgid=ug-pg" in call
        assert "UltimaReadFilter,rgid=ont" not in call
        assert r"ug=ID:ug\tSM:donor\tLR:0" in call
        assert r"ont=ID:ont\tSM:donor\tLR:1" in call
        assert str(profile.outputs["lifted_alignment"]) in call
    for name in ("dnascope", "model-apply"):
        assert str(p.model_bundle / "dnascope.model") in str(graph[name].shell)
    for name in ("longreadsv", "graph-update", "graph-update-raw"):
        assert "UltimaReadFilter" not in str(graph[name].shell)
        assert str(p.sr_aln[0]) not in str(graph[name].shell)
    assert str(p.model_bundle / "longreadsv.model") in str(graph["longreadsv"].shell)
    assert {j.name for j in dag.waiting_jobs[graph["index-small_variants"]]} == {"model-apply"}
    assert {j.name for j in dag.waiting_jobs[graph["index-structural_variants"]]} == {"pangenome-sv"}
    assert {j.name for j in dag.waiting_jobs[graph["index-lifted-alignment"]]} == {"mm2-lift"}
    assert graph["index-lifted-alignment"] in dag.waiting_jobs[graph["dnascope"]]
    assert graph["index-lifted-alignment"] in dag.waiting_jobs[graph["pangenome-sv"]]
    assert "--tbi" in str(graph["index-small_variants"].shell)


def test_illumina_route_retains_upstream_mapping_and_no_ultima_filter(candidate):
    p, _ = candidate
    p.experimental_ultima = False
    p.ultima_profile = None
    dag = p.build_dag()
    graph = jobs(dag)
    assert str(p.model_bundle / "minimap2.model") in str(graph["mm2-lift"].shell)
    assert "--secondary=yes" in str(graph["mm2-lift"].shell)
    assert "UltimaReadFilter" not in str(graph["dnascope"].shell)
    assert "index-small_variants" not in graph


@pytest.mark.parametrize("flag,value", [
    ("r1_fastq", [Path("reads.fq")]), ("r2_fastq", [Path("reads.fq")]),
    ("lr_align_input", True), ("rgsm", "override"), ("call_cnvs", True),
    ("segdup_caller", []), ("skip_model_apply", True),
    ("skip_small_variants", True), ("skip_svs", True),
    ("skip_version_check", True), ("skip_pop_vcf_id_check", True),
    ("skip_contig_checks", True), ("skip_pangenome_name_checks", True),
    ("t1k_hla_seq", Path("hla.fa")), ("expansion_catalog", Path("repeats.json")),
])
def test_unsupported_options_fail(candidate, flag, value):
    p, profile = candidate
    p.pangenome_ref_name = p.pangenome_contig_prefix = None
    setattr(p, flag, value)
    with pytest.raises(ValueError, match="Unsupported"):
        profile.validate_options()


def test_required_short_read_model_and_opt_in(candidate):
    p, profile = candidate
    p.sr_model_bundle = None
    with pytest.raises(ValueError, match="requires --sr_model_bundle"):
        profile.validate_options()
    p.experimental_ultima = False
    p.sr_model_bundle = Path("ultima.bundle")
    with pytest.raises(ValueError, match="requires --experimental_ultima"):
        p.validate()


def test_real_headers_used_in_dry_runs_and_dicts_checked(candidate, monkeypatch):
    p, profile = candidate
    seen = []
    def read(command, **kwargs):
        seen.append(command)
        return SimpleNamespace(stdout=header() if command[-1].endswith("ug.bam") else header("ont", platform="ONT"))
    monkeypatch.setattr(up.subprocess, "run", read)
    profile.collect_readgroups()
    p.validate_readgroups()
    assert p.sample_sm == "donor"
    assert len(seen) == 2 and all("--reference" in cmd for cmd in seen)
    monkeypatch.setattr(up.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=header(length=900)))
    with pytest.raises(ValueError, match="dictionary"):
        profile.collect_readgroups()


@pytest.mark.parametrize("groups", [
    [[{"ID": "ug", "SM": "other"}]],
    [[{"ID": "ug", "SM": "donor"}]],
    [[{"ID": "ug-pg", "SM": "donor"}]],
    [[{"ID": "ont", "SM": ""}]],
    [],
])
def test_mismatched_sample_or_readgroups_rejected_in_dry_run(candidate, groups):
    p, _ = candidate
    p.lr_readgroups = groups if groups else [[]]
    with pytest.raises(SystemExit):
        p.validate_readgroups()


@pytest.mark.parametrize("text", [
    header().replace("SO:coordinate", "SO:unsorted"),
    header().replace("LN:1000", "LN:invalid"),
    header().replace("ID:ug", "ID:ug,ont"),
    header().replace("SM:donor", "SM:"),
    header() + "@SQ\tSN:chr1\tLN:1000\n",
])
def test_malformed_alignment_headers(text):
    with pytest.raises(ValueError):
        up.parse_header(text)


def test_missing_index_and_duplicate_marking_evidence(candidate, monkeypatch):
    p, profile = candidate
    monkeypatch.setattr(up.subprocess, "run", lambda *a, **k: SimpleNamespace(stdout=header().split("@PG")[0]))
    with pytest.raises(ValueError, match="duplicate-marking"):
        profile.collect_readgroups()
    Path(str(p.sr_aln[0]) + ".bai").unlink()
    with pytest.raises(ValueError, match="Missing alignment index"):
        profile.collect_readgroups()


def fake_bundles(p, monkeypatch):
    joint = {
        "pipeline": "Hybrid pangenome", "shortReadPlatform": "Illumina",
        "longReadPlatform": "ONT", "bundleVersion": "1.0",
        "SentieonVcfID": up.POPULATION_ID, "pangenome": up.GRAPH,
        "minScriptVersion": "2.0.0",
    }
    ultima = {
        "pipeline": "Sentieon pangenome", "platform": "Ultima",
        "bundleVersion": "1.3", "minScriptVersion": "1.5.0",
        "pangenome": "hprc-v2.0-mc-grch38.gbz",
        "SentieonVcfID": "population-hprc-v2.0+gnomad-v4.1.0-20251216",
    }
    archives = {
        str(p.model_bundle): {"bundle_info.json": json.dumps(joint).encode(),
                             **{name: name.encode() for name in ("dnascope.model", "extract.model", "longreadsv.model")}},
        str(p.sr_model_bundle): {"bundle_info.json": json.dumps(ultima).encode(),
                                "minimap2.model": b"mapper fixture"},
    }
    def load(path):
        if path in archives:
            return list(archives[path])
        directory, member = str(Path(path).parent), Path(path).name
        return archives[directory].get(member, [])
    monkeypatch.setattr(up, "ar_load", load)
    monkeypatch.setattr(up, "__version__", "2.0.0+i.ultima.dev0")
    monkeypatch.setattr(up, "ULTIMA_MAPPER_SHA256", hashlib.sha256(b"mapper fixture").hexdigest())
    monkeypatch.setattr(up, "LONGREADSV_SHA256", hashlib.sha256(b"longreadsv.model").hexdigest())
    return archives


def test_model_roles_fingerprint_immutable_bundles(candidate, monkeypatch):
    p, profile = candidate
    fake_bundles(p, monkeypatch)
    before = [path.read_bytes() for path in (p.model_bundle, p.sr_model_bundle)]
    profile.validate_bundles()
    models = profile.data["models"]
    assert models["joint_calling_and_model_apply"]["path"] == str(p.model_bundle / "dnascope.model")
    assert models["ultima_graph_alignment_and_liftover"]["path"] == str(p.sr_model_bundle / "minimap2.model")
    assert [path.read_bytes() for path in (p.model_bundle, p.sr_model_bundle)] == before
    assert all(role["sha256"] for role in models.values())


@pytest.mark.parametrize("damage", ["missing_member", "platform", "mapper_bytes"])
def test_incompatible_models_fail(candidate, monkeypatch, damage):
    p, profile = candidate
    archives = fake_bundles(p, monkeypatch)
    if damage == "missing_member":
        del archives[str(p.model_bundle)]["extract.model"]
    elif damage == "platform":
        info = json.loads(archives[str(p.model_bundle)]["bundle_info.json"])
        info["shortReadPlatform"] = "Ultima"
        archives[str(p.model_bundle)]["bundle_info.json"] = json.dumps(info).encode()
    else:
        archives[str(p.sr_model_bundle)]["minimap2.model"] = b"wrong model"
    with pytest.raises(ValueError):
        profile.validate_bundles()


def test_graph_and_population_mismatch_fail(candidate, monkeypatch):
    p, profile = candidate
    graph = PangenomeReference("GRCh38", "GRCh38#0#", ["chr1"], ["GRCh38"], 1)
    hapl = HaplHeader(6, 1, 1, 1, 1, 29)
    monkeypatch.setattr(up, "detect_pangenome_reference", lambda path: graph)
    monkeypatch.setattr(up, "read_hapl_header", lambda path: hapl)
    monkeypatch.setattr(up, "detect_reference_build", lambda data: "hg38")
    hapl.top_level_chains = 2
    with pytest.raises(ValueError, match="HAPL"):
        profile.validate_assets()
    hapl.top_level_chains = 1
    p.pop_vcf_header[1] = "##SentieonVcfID=wrong"
    with pytest.raises(SystemExit):
        profile.validate_assets()
    p.pop_vcf_header[1] = f"##SentieonVcfID={up.POPULATION_ID}"
    p.pop_vcf_contigs["chr1"] = 999
    with pytest.raises(SystemExit):
        profile.validate_assets()


@pytest.mark.parametrize("error,status", [
    (RuntimeError("tool failed"), "failed"),
    (KeyboardInterrupt(), "interrupted"),
    (InterruptedError("signal 15"), "interrupted"),
])
def test_error_receipt_never_claims_completion(candidate, error, status):
    p, profile = candidate
    profile.finish(False, error)
    receipt = json.loads(profile.receipt.read_text())
    assert receipt["status"] == status
    assert receipt["experimental"] is True
    assert receipt["scientific_validation"] == "pending"
    assert receipt["production_accepted"] is False


def test_missing_output_cannot_be_completed(candidate):
    p, profile = candidate
    p.dry_run = False
    with pytest.raises(FileNotFoundError):
        profile.finish(True, None)
    assert json.loads(profile.receipt.read_text())["status"] == "failed"


def materialize_outputs(p, profile):
    p.dry_run = False
    profile.data["dry_run"] = False
    for path in profile.outputs.values():
        path.write_bytes(b"synthetic output")
    profile.outputs["ploidy"].write_text('{"sex": "Unknown", "contigs": {}}')
    directory = p.output_vcf.parent / "logs"
    directory.mkdir()
    paths = {
        key: directory / key for key in (
            "run_log", "command_txt", "process_metrics", "job_metrics",
        )
    }
    for path in paths.values():
        path.write_text("header\nrow\n")
    p.run_logs = SimpleNamespace(log_dir=directory, **paths)


def test_completion_requires_indexes_and_preserves_experimental_status(candidate):
    p, profile = candidate
    materialize_outputs(p, profile)
    profile.finish(True, None)
    receipt = json.loads(profile.receipt.read_text())
    assert receipt["status"] == "completed"
    assert receipt["experimental"] and not receipt["production_accepted"]
    assert len(receipt["outputs"]) == 7
    assert receipt["outputs"]["small_variants_index"]["bytes"] > 0


def test_missing_index_fails_even_when_variant_files_exist(candidate):
    p, profile = candidate
    materialize_outputs(p, profile)
    profile.outputs["structural_variants_index"].unlink()
    with pytest.raises(FileNotFoundError):
        profile.finish(True, None)
    assert json.loads(profile.receipt.read_text())["status"] == "failed"


def test_missing_metrics_prevents_complete_receipt(candidate):
    p, profile = candidate
    materialize_outputs(p, profile)
    p.run_logs.job_metrics.write_text("header\n")
    with pytest.raises(ValueError, match="resource metric"):
        profile.finish(True, None)
    assert json.loads(profile.receipt.read_text())["status"] == "failed"


def test_changed_inputs_prevent_complete_receipt(candidate):
    p, profile = candidate
    materialize_outputs(p, profile)
    profile.frozen = [up.file_identity(p.sr_aln[0])]
    p.sr_aln[0].write_bytes(b"modified input fixture")
    with pytest.raises(ValueError, match="changed during execution"):
        profile.finish(True, None)
    assert json.loads(profile.receipt.read_text())["status"] == "failed"


def test_dry_run_never_becomes_completed(candidate):
    p, profile = candidate
    profile.finish(True, None)
    assert json.loads(profile.receipt.read_text())["status"] == "dry_run"


def test_existing_receipt_is_not_overwritten(candidate):
    p, profile = candidate
    before = profile.receipt.read_bytes()
    other = up.UltimaProfile(p)
    with pytest.raises(FileExistsError):
        other.start()
    other.finish(False, RuntimeError("collision"))
    assert profile.receipt.read_bytes() == before


def test_signal_is_not_reported_as_success_even_after_dag_drains(candidate):
    p, _ = candidate
    with pytest.raises(InterruptedError, match="signal 15"):
        p.check_execution(None, SimpleNamespace(interrupted_signal=15))


def test_shared_lifecycle_records_execution_failure(candidate, monkeypatch):
    p, profile = candidate
    monkeypatch.setattr(p, "validate", lambda: None)
    monkeypatch.setattr(p, "build_dag", lambda: SimpleNamespace(waiting_jobs={}, ready_jobs={}))
    monkeypatch.setattr(p, "run", lambda dag: SimpleNamespace(jobs_with_errors=["failed-tool"]))
    with pytest.raises(DagExecutionError, match="failed-tool"):
        p.main(argparse.Namespace(loglevel="WARNING"))
    assert json.loads(profile.receipt.read_text())["status"] == "failed"


def test_new_arguments_are_registered():
    parser = argparse.ArgumentParser()
    HybridPangenome.add_arguments(parser)
    options = {flag for action in parser._actions for flag in action.option_strings}
    assert "--experimental_ultima" in options
    assert "--sr_model_bundle" in options
