"""Validation and provenance for the fixed experimental Ultima+ONT profile.

The DAG belongs to HybridPangenome. This module does not train, modify, or
repackage vendor models, and never substitutes a model when validation fails.
"""

from __future__ import annotations

import asyncio
import dataclasses
import datetime
import hashlib
import json
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from typing import TYPE_CHECKING, Any, Iterable

from packaging.version import Version

from .archive import ar_load
from .dag import DAG
from .job import Job
from .pangenome_meta import detect_pangenome_reference, read_hapl_header
from .shell_pipeline import Command, Pipeline
from .shard import detect_reference_build
from .util import __version__, executable_version, parse_rg_line

if TYPE_CHECKING:
    from .hybrid_pangenome import HybridPangenome


PROFILE = "experimental-ultima-ont-hprc-v2.1-v1"
GRAPH = "hprc-v2.1-mc-grch38.gbz"
HAPLOTYPES = "hprc-v2.1-mc-grch38.hapl"
POPULATION_ID = "population-hprc-v2.0-20260528"
GRAPH_SHA256 = "11d6047f79575ffb83757462484bad134ed20928bd2c8171ec52e35a54976e2b"
HAPLOTYPES_SHA256 = "dfc29be8818a5630f327b8882a11824b7974fa67e957cafbb53df0159e395d37"
ULTIMA_MAPPER_SHA256 = (
    "20417e789fea9ff03063ad54cfe171cef5a75f0c1396c8875e3685abdc70ea99"
)
LONGREADSV_SHA256 = (
    "2467ce218f6b9e9bd65f454fb08ba8b90f1eb6cdd7cff051ba964db598471556"
)


def utc_now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_hapl_structure(hapl: Any) -> None:
    """Check the fixed profile's k and a populated snarl-chain index.

    Top-level chains belong to the snarl decomposition, not reference paths.
    The selected vendor v2.1 pair has 184 chains and 195 reference paths.
    Exact GBZ/HAPL content hashes below establish the selected pair.
    """
    if (hapl.k != 29 or hapl.top_level_chains <= 0
            or hapl.construction_jobs <= 0
            or hapl.total_subchains < hapl.top_level_chains
            or hapl.total_kmers <= 0):
        raise ValueError("HAPL structure is incompatible with the fixed profile")


def file_identity(path: Path) -> dict[str, Any]:
    stat = path.stat()
    if not path.is_file() or stat.st_size == 0:
        raise ValueError(f"Expected a nonempty regular file: {path}")
    return {
        "path": str(path.absolute()),
        "resolved_path": str(path.resolve()),
        "bytes": stat.st_size,
        "mtime_ns": stat.st_mtime_ns,
    }


def alignment_indexes(path: Path) -> list[Path]:
    """Recognized native index formats, with no generated replacement."""
    suffixes = [".crai"] if path.suffix.lower() == ".cram" else [".bai", ".csi"]
    candidates = [Path(str(path) + suffix) for suffix in suffixes]
    candidates.extend(path.with_suffix(suffix) for suffix in suffixes)
    indexes = [candidate for candidate in candidates if candidate.is_file()]
    if not indexes:
        raise ValueError(f"Missing alignment index for {path}")
    return indexes


def parse_header(
    header: str,
) -> tuple[list[dict[str, str]], list[tuple[str, int]]]:
    """Check coordinate sorting, ordered reference dictionary, and RG syntax."""
    records: dict[str, list[dict[str, str]]] = {}
    for line in header.splitlines():
        if not line.startswith(("@HD\t", "@SQ\t", "@RG\t", "@PG\t")):
            continue
        fields = line.split("\t")
        tags: dict[str, str] = {}
        for field in fields[1:]:
            key, sep, value = field.partition(":")
            if not sep or key in tags or not value:
                raise ValueError(
                    f"Malformed or duplicate SAM header field: {field!r}"
                )
            tags[key] = value
        records.setdefault(fields[0], []).append(tags)
    hd = records.get("@HD", [])
    if len(hd) != 1 or hd[0].get("SO") != "coordinate":
        raise ValueError("Input alignment must declare @HD SO:coordinate")
    sq = records.get("@SQ", [])
    try:
        dictionary = [(entry["SN"], int(entry["LN"])) for entry in sq]
    except (KeyError, ValueError) as exc:
        raise ValueError("Every @SQ requires SN and an integer LN") from exc
    if not dictionary or len({name for name, _ in dictionary}) != len(dictionary):
        raise ValueError("Input alignment has a missing or duplicate @SQ dictionary")
    if any(length <= 0 for _, length in dictionary):
        raise ValueError("Input alignment has a nonpositive @SQ length")
    groups = [
        parse_rg_line(line) for line in header.splitlines()
        if line.startswith("@RG\t")
    ]
    if not groups:
        raise ValueError("Input alignment must contain @RG records")
    for group in groups:
        rg_id, sample = group.get("ID", ""), group.get("SM", "")
        # These delimiters have meaning in the driver's rgid/replace_rg syntax.
        if not re.fullmatch(r"[!-~]+", rg_id) or any(c in rg_id for c in ",=\\"):
            raise ValueError(f"Invalid read-group ID for driver routing: {rg_id!r}")
        if not sample or any(c in sample for c in "\t\r\n\\"):
            raise ValueError("Each input read group requires a valid SM tag")
    return groups, dictionary


class ReceiptMessages(logging.Handler):
    """Keep bounded validation errors even before native file logs start."""

    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.messages.append(record.getMessage()[:2000])
        self.messages = self.messages[-50:]


class UltimaProfile:
    """A receipt owned by one invocation and the fixed profile's preflight."""

    def __init__(self, pipeline: HybridPangenome):
        self.p = pipeline
        self.receipt: Path | None = None
        self.owned = False
        self.outputs: dict[str, Path] = {}
        self.frozen: list[dict[str, Any]] = []
        self.messages = ReceiptMessages()
        self.data: dict[str, Any] = {
            "schema_version": 1,
            "profile": PROFILE,
            "experimental": True,
            "scientific_validation": "pending",
            "production_accepted": False,
            "status": "validating",
            "started_at": utc_now(),
            "cli_version": __version__,
            "python_version": sys.version,
            "python_executable": sys.executable,
            "argv": list(sys.argv),
            "dry_run": pipeline.dry_run,
            "model_composition": (
                "Illumina+ONT joint model with Ultima pangenome mapper; "
                "cross-platform accuracy is unvalidated"
            ),
            "requested_inputs": {
                name: self._paths(getattr(pipeline, name))
                for name in (
                    "reference", "gbz", "hapl", "pop_vcf", "bed", "dbsnp",
                    "model_bundle", "sr_model_bundle", "sr_aln", "lr_aln",
                )
            },
        }

    @staticmethod
    def _paths(value: Any) -> Any:
        if isinstance(value, list):
            return [str(path.absolute()) for path in value]
        return str(value.absolute()) if value is not None else None

    def start(self) -> None:
        p = self.p
        p.validate_output_vcf()
        assert p.output_vcf is not None
        stem = str(p.output_vcf)[:-len(".vcf.gz")]
        suffix = "bam" if p.bam_format else "cram"
        lift = Path(f"{stem}_lift_deduped.{suffix}")
        self.outputs = {
            "small_variants": p.output_vcf,
            "small_variants_index": Path(str(p.output_vcf) + ".tbi"),
            "structural_variants": Path(stem + "_sv.vcf.gz"),
            "structural_variants_index": Path(stem + "_sv.vcf.gz.tbi"),
            "ploidy": Path(stem + "_ploidy.json"),
            "lifted_alignment": lift,
            "lifted_alignment_index": Path(
                str(lift) + (".bai" if p.bam_format else ".crai")
            ),
        }
        self.receipt = Path(stem + "_provenance.json")
        # Never replace a prior success receipt or mistake stale output for this run.
        with self.receipt.open("x", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2)
            handle.write("\n")
        self.owned = True
        logging.getLogger("sentieon_cli").addHandler(self.messages)
        for path in self.outputs.values():
            if path.exists():
                raise ValueError(f"Output already exists; use a fresh output prefix: {path}")
        log_dir = p.log_dir if p.log_dir is not None else Path(stem + "_logs")
        if log_dir.exists() and (not log_dir.is_dir() or any(log_dir.iterdir())):
            raise ValueError(f"Experimental runs require a fresh log directory: {log_dir}")

    def save(self) -> None:
        assert self.receipt is not None and self.owned
        # Atomic replacement avoids a partially written terminal receipt.
        fd, name = tempfile.mkstemp(prefix=".provenance-", dir=self.receipt.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(self.data, handle, indent=2, sort_keys=True)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(name, self.receipt)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def validate_options(self) -> None:
        p = self.p
        if p.sr_model_bundle is None:
            raise ValueError("--experimental_ultima requires --sr_model_bundle")
        if not p.sr_aln or not p.lr_aln:
            raise ValueError("Ultima mode requires aligned --sr_aln and --lr_aln")
        forbidden = (
            "r1_fastq", "r2_fastq", "readgroup", "lr_align_input", "lr_input_ref",
            "rgsm", "call_cnvs", "expansion_catalog", "t1k_hla_seq", "t1k_hla_coord",
            "t1k_kir_seq", "t1k_kir_coord", "skip_model_apply", "skip_small_variants",
            "skip_svs", "skip_version_check", "skip_pop_vcf_id_check",
            "skip_contig_checks", "skip_pangenome_name_checks",
            "pangenome_ref_name", "pangenome_contig_prefix", "par_bed", "sample_sex",
        )
        supplied = ["--" + name for name in forbidden if getattr(p, name)]
        if p.segdup_caller is not None:
            supplied.append("--segdup_caller")
        if supplied:
            raise ValueError("Unsupported in experimental Ultima mode: " + ", ".join(supplied))
        if p.cores < 1 or p.kmer_memory < 1:
            raise ValueError("--cores and --kmer_memory must be positive")
        for path in p.sr_aln + p.lr_aln:
            if path.suffix.lower() not in (".bam", ".cram"):
                raise ValueError(f"Expected aligned BAM/CRAM input: {path}")

    def validate_bundles(self) -> None:
        p = self.p
        roles = {}
        profiles = (
            (p.model_bundle, {
                "pipeline": "Hybrid pangenome", "shortReadPlatform": "Illumina",
                "longReadPlatform": "ONT", "bundleVersion": "1.0",
                "SentieonVcfID": POPULATION_ID, "pangenome": GRAPH,
                "minScriptVersion": "2.0.0",
            }, {"dnascope.model", "extract.model", "longreadsv.model"}),
            (p.sr_model_bundle, {
                "pipeline": "Sentieon pangenome", "platform": "Ultima",
                "bundleVersion": "1.3", "minScriptVersion": "1.5.0",
                "pangenome": "hprc-v2.0-mc-grch38.gbz",
                "SentieonVcfID": "population-hprc-v2.0+gnomad-v4.1.0-20251216",
            }, {"minimap2.model"}),
        )
        bundles = []
        for bundle, expected, required in profiles:
            assert bundle is not None
            identity = file_identity(bundle)
            members = ar_load(str(bundle))
            if not isinstance(members, list) or not required.issubset(members):
                raise ValueError(f"Missing required model members in {bundle}: {sorted(required)}")
            raw = ar_load(str(bundle / "bundle_info.json"))
            if not isinstance(raw, bytes):
                raise ValueError(f"Missing bundle_info.json in {bundle}")
            info = json.loads(raw)
            if not isinstance(info, dict) or any(info.get(k) != v for k, v in expected.items()):
                raise ValueError(f"Bundle metadata does not match fixed experimental profile: {bundle}")
            if Version(info["minScriptVersion"]) > Version(__version__):
                raise ValueError("Install the refreshed CLI before using these bundles")
            identity["sha256"] = sha256_file(bundle)
            identity["vendor_metadata"] = info
            bundles.append(identity)
            for member in sorted(required):
                payload = ar_load(str(bundle / member))
                if not isinstance(payload, bytes) or not payload:
                    raise ValueError(f"Empty or unreadable model: {bundle / member}")
                digest = hashlib.sha256(payload).hexdigest()
                expected_digest = {
                    "minimap2.model": ULTIMA_MAPPER_SHA256,
                    "longreadsv.model": LONGREADSV_SHA256,
                }.get(member)
                if expected_digest is not None and digest != expected_digest:
                    raise ValueError(f"Model differs from the selected released member: {bundle / member}")
                roles[member] = {
                    "path": str((bundle / member).absolute()),
                    "bundle_sha256": identity["sha256"],
                    "sha256": digest, "bytes": len(payload),
                }
            self.frozen.append(file_identity(bundle))
        self.data["bundles"] = bundles
        self.data["models"] = {
            "joint_calling_and_model_apply": roles["dnascope.model"],
            "graph_read_extraction": roles["extract.model"],
            "ultima_graph_alignment_and_liftover": roles["minimap2.model"],
            "ont_structural_variants": roles["longreadsv.model"],
        }
        p.extract_model_name = "extract.model"
        self.save()

    def collect_readgroups(self) -> None:
        """Inspect real headers even in dry runs; never use synthetic RGs."""
        p = self.p
        reference_dictionary = [(name, data["length"]) for name, data in p.fai_data.items()]
        inputs = []
        checksums: dict[str, str] = {}
        p.sr_readgroups, p.lr_readgroups = [], []
        for platform, paths, destination in (
            ("ULTIMA", p.sr_aln, p.sr_readgroups),
            ("ONT", p.lr_aln, p.lr_readgroups),
        ):
            for path in paths:
                identity = file_identity(path)
                indexes = [file_identity(index) for index in alignment_indexes(path)]
                result = subprocess.run(
                    ["samtools", "view", "--no-PG", "-H", "--reference", str(p.reference), str(path)],
                    check=True, capture_output=True, text=True,
                )
                groups, dictionary = parse_header(result.stdout)
                if dictionary != reference_dictionary:
                    raise ValueError(f"Reference dictionary/order differs from FASTA index: {path}")
                if any(group.get("PL", "").upper() != platform for group in groups):
                    raise ValueError(f"All @RG PL tags in {path} must be {platform}")
                # Compare sequence checksums wherever headers supply them.
                for line in result.stdout.splitlines():
                    if line.startswith("@SQ\t"):
                        tags = dict(field.split(":", 1) for field in line.split("\t")[1:])
                        if "M5" in tags:
                            name, checksum = tags["SN"], tags["M5"].lower()
                            if name in checksums and checksums[name] != checksum:
                                raise ValueError(f"Conflicting @SQ M5 for {name} in {path}")
                            checksums[name] = checksum
                if platform == "ULTIMA":
                    pg = "\n".join(line for line in result.stdout.splitlines() if line.startswith("@PG\t"))
                    if not re.search(r"\b(?:Dedup|MarkDuplicates\w*|markdup)\b", pg, re.IGNORECASE):
                        raise ValueError(f"No duplicate-marking @PG evidence in Ultima input: {path}")
                destination.append(groups)
                identity.update({
                    "platform": platform, "indexes": indexes, "readgroups": groups,
                    "header_sha256": hashlib.sha256(result.stdout.encode()).hexdigest(),
                    "duplicate_marking_evidence": "header @PG" if platform == "ULTIMA" else "not required",
                })
                inputs.append(identity)
                self.frozen.extend([file_identity(path), *indexes])
        self.data["alignments"] = inputs
        self.data["reference_dictionary"] = reference_dictionary
        self.data["alignment_m5_checksums"] = checksums
        self.save()

    def validate_assets(self) -> None:
        p = self.p
        assert p.gbz is not None and p.hapl is not None and p.reference is not None
        assert p.pop_vcf is not None
        if p.gbz.name != GRAPH or p.hapl.name != HAPLOTYPES:
            raise ValueError(f"This profile requires the named vendor pair {GRAPH} / {HAPLOTYPES}")
        graph = detect_pangenome_reference(p.gbz)
        hapl = read_hapl_header(p.hapl)
        if graph.ref_name != "GRCh38" or graph.contig_prefix != "GRCh38#0#":
            raise ValueError("Experimental profile requires the GRCh38 pangenome backbone")
        if detect_reference_build(p.fai_data) != "hg38":
            raise ValueError("Experimental profile requires a GRCh38 reference dictionary")
        validate_hapl_structure(hapl)
        reference_hashes = {"gbz": sha256_file(p.gbz), "hapl": sha256_file(p.hapl)}
        if (reference_hashes["gbz"] != GRAPH_SHA256
                or reference_hashes["hapl"] != HAPLOTYPES_SHA256):
            raise ValueError("GBZ/HAPL content differs from the selected vendor v2.1 pair")
        if not p.pop_vcf_header or not p.pop_vcf_contigs:
            raise ValueError("A readable population VCF header with contig lengths is required")
        p.check_pop_vcf_id(POPULATION_ID)
        # Dry runs must satisfy the same real graph/population checks as live runs.
        p.check_pangenome_reference_fasta(graph)
        p.pangenome_reference = graph
        p.validate_pangenome_contig_lengths()
        indexes = [Path(str(p.pop_vcf) + suffix) for suffix in (".tbi", ".csi")]
        indexes = [index for index in indexes if index.is_file()]
        if not indexes:
            raise ValueError("The population VCF requires its .tbi or .csi index")
        reference_files = [p.reference, Path(str(p.reference) + ".fai"), p.gbz, p.hapl, p.pop_vcf, *indexes]
        reference_files.extend(path for path in (p.bed, p.dbsnp) if path is not None)
        self.data["reference_assets"] = [file_identity(path) for path in reference_files]
        self.frozen.extend(file_identity(path) for path in reference_files)
        self.data["reference_fai_sha256"] = sha256_file(Path(str(p.reference) + ".fai"))
        package_dir = Path(__file__).parent
        self.data["cli_source_sha256"] = {
            str(path.relative_to(package_dir)): sha256_file(path)
            for path in sorted(package_dir.rglob("*.py"))
        }
        self.data["graph_metadata"] = dataclasses.asdict(graph)
        self.data["haplotype_metadata"] = dataclasses.asdict(hapl)
        self.data["reference_pair_sha256"] = reference_hashes
        self.data["reference_pair_verification"] = (
            "Pinned GBZ/HAPL content hashes observed from the selected vendor v2.1 "
            "download pair; GRCh38 backbone, HAPL k/structure and population "
            "contig consistency. No vendor-signed checksum manifest was supplied"
        )
        tools = {}
        for command in ("sentieon driver", "samtools", "bcftools", "vg", "kmc", "bedtools"):
            executable = shutil.which(command.split()[0])
            if executable is None:
                raise ValueError(f"Missing required executable: {command}")
            # vg/KMC version banners do not follow the generic parser's format.
            # Retain the raw bounded banner and executable digest as provenance.
            probe = subprocess.run(
                command.split() + ["--version"], capture_output=True,
                text=True, timeout=30,
            )
            tools[command] = {
                "version_output": (probe.stdout + probe.stderr)[:4096],
                "version_exit_code": probe.returncode,
                "executable": executable,
                "executable_sha256": sha256_file(Path(executable)),
            }
        driver_version = executable_version("sentieon driver")
        if driver_version is None or driver_version < Version("202503.04"):
            raise ValueError("Experimental Ultima mode requires Sentieon 202503.04 or later")
        tools["sentieon driver"]["version"] = str(driver_version)
        self.data.update({
            "tools": tools, "sample": p.sample_sm,
            "read_group_channels": {"original_ultima": 0, "ont": 1, "lifted_ultima": 2},
            "ultima_read_filters": p.ultima_read_filters(),
            "parameters": {"cores": p.cores, "kmer_memory_gb": p.kmer_memory, "pcr_free": p.pcr_free},
            "status": "running" if not p.dry_run else "planning",
        })
        p.logger.warning("Experimental Ultima+ONT joint model composition; scientific validation is pending")
        self.save()

    def add_indexes(
        self, dag: DAG, small_deps: Iterable[Job], sv_job: Job,
    ) -> None:
        for role, upstream in (
            ("small_variants", set(small_deps)),
            ("structural_variants", {sv_job}),
        ):
            command = Command(
                "bcftools", "index", "--tbi", "--force",
                str(self.outputs[role]),
            )
            job = Job(
                Pipeline(command), f"index-{role}", 1, task_name="indexing",
            )
            dag.add_job(job, upstream)

    def add_lift_index(self, dag: DAG, lift_job: Job) -> Job:
        """Finish the lifted index before either joint caller opens it."""
        command = Command(
            "samtools", "index", "-@", str(max(0, self.p.cores - 1)),
            str(self.outputs["lifted_alignment"]),
            str(self.outputs["lifted_alignment_index"]),
        )
        job = Job(
            Pipeline(command),
            "index-lifted-alignment", self.p.cores, task_name="indexing",
        )
        dag.add_job(job, {lift_job})
        return job

    def finish(self, success: bool, error: BaseException | None) -> None:
        if not self.owned:
            return
        logging.getLogger("sentieon_cli").removeHandler(self.messages)
        self.messages.close()
        self.data["messages"] = self.messages.messages
        failure: BaseException | None = error
        if success and not self.p.dry_run:
            try:
                for identity in self.frozen:
                    if file_identity(Path(identity["path"])) != identity:
                        raise ValueError(f"Input or asset changed during execution: {identity['path']}")
                self.data["outputs"] = {role: file_identity(path) for role, path in self.outputs.items()}
                ploidy = json.loads(self.outputs["ploidy"].read_text())
                if not isinstance(ploidy, dict) or "sex" not in ploidy:
                    raise ValueError("Ploidy output is not the expected JSON report")
                if self.p.run_logs is None:
                    raise ValueError("Native run logs were not created")
                logs = self.p.run_logs
                self.data["log_files"] = [
                    file_identity(path) for path in (
                        logs.run_log, logs.command_txt,
                        logs.process_metrics, logs.job_metrics,
                    )
                ]
                for path in (logs.process_metrics, logs.job_metrics):
                    with path.open() as handle:
                        handle.readline()
                        if not handle.readline().strip():
                            raise ValueError(f"No resource metric rows recorded in {path}")
            except Exception as exc:
                failure = exc
                success = False
        interrupted = isinstance(
            failure, (InterruptedError, KeyboardInterrupt, asyncio.CancelledError)
        )
        if isinstance(failure, SystemExit) and failure.code in (130, 143, -2, -15):
            interrupted = True
        if success:
            self.data["status"] = "dry_run" if self.p.dry_run else "completed"
        else:
            self.data["status"] = "interrupted" if interrupted else "failed"
        self.data["finished_at"] = utc_now()
        self.data["expected_outputs"] = {role: str(path.absolute()) for role, path in self.outputs.items()}
        if failure is not None:
            self.data["error"] = {"type": type(failure).__name__, "message": str(failure)}
        if self.p.run_logs is not None:
            self.data["logs"] = str(self.p.run_logs.log_dir.absolute())
            self.data["resource_metrics"] = [
                str(self.p.run_logs.process_metrics.absolute()),
                str(self.p.run_logs.job_metrics.absolute()),
            ]
        if hasattr(self.p, "tmp_dir"):
            self.data["temporary_directory"] = str(self.p.tmp_dir.absolute())
            self.data["temporary_directory_retained"] = self.p.tmp_dir.exists()
        self.save()
        if failure is not None and failure is not error:
            raise failure
