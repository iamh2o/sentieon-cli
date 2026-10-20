"""Vendor duplicate evidence is explicit, typed and bound to prepared bytes."""
import hashlib
import json
from types import SimpleNamespace

import pytest

from sentieon_cli import ultima_duplicate_marking as duplicate
from sentieon_cli import ultima_pangenome
from sentieon_cli.hybrid_pangenome import HybridPangenome


@pytest.fixture
def vendor(tmp_path):
    alignment = tmp_path / "prepared.cram"
    alignment.write_bytes(b"newly prepared alignment fixture")
    provenance = tmp_path / "accepted-source.json"
    provenance.write_text('{"source":"accepted immutable vendor delivery"}\n')
    header = (
        "@HD\tVN:1.6\tSO:coordinate\n"
        "@SQ\tSN:chr1\tLN:1000\n"
        "@RG\tID:ug\tSM:HG002\tPL:ULTIMA\n"
        "@PG\tID:demux_0\tPN:demux\tVN:1.5.18\tCL:demux --umi=u5,u3 --mark-duplicates-ends-read-uncertainty=0\n"
        "@PG\tID:sorter_0\tPN:sorter\tVN:1.5.18\tCL:sorter --runid=vendor\n"
    )
    groups = [{"ID": "ug", "SM": "HG002", "PL": "ULTIMA"}]
    entry = {
        "alignment": {"path": str(alignment), "bytes": alignment.stat().st_size,
                      "sha256": duplicate.sha256_file(alignment),
                      "header_sha256": hashlib.sha256(header.encode()).hexdigest()},
        "source": {"s3_uri": "s3://accepted-vendor/source.cram", "bytes": 1000,
                   "header_sha256": "a" * 64,
                   "accepted_provenance_path": str(provenance),
                   "accepted_provenance_sha256": duplicate.sha256_file(provenance)},
        "vendor_program_ids": ["demux_0", "sorter_0"], "state": "marked",
        "flags_preserved": True, "selected_flags_sha256": "b" * 64,
        "prepared_flags_sha256": "b" * 64,
        "selected_read_groups": {"ug": {"primary_records": 100, "duplicate_primary_records": 7}},
        "prepared_read_groups": {"ug": {"primary_records": 100, "duplicate_primary_records": 7}},
    }
    receipt = tmp_path / "duplicate-receipt.json"
    receipt.write_text(json.dumps({"schema": duplicate.SCHEMA, "status": "completed", "alignments": [entry]}))
    return alignment, provenance, header, groups, entry, receipt


def test_vendor_without_named_markdup_program_requires_bound_positive_flags(vendor):
    alignment, provenance, header, groups, entry, receipt = vendor
    entries, identity = duplicate.load_receipt(receipt, [alignment])
    evidence = duplicate.validate_alignment(entries[str(alignment.resolve())], alignment, header, groups)
    assert evidence["observed_duplicate_primary_records"] == 7
    assert evidence["source"]["s3_uri"] == "s3://accepted-vendor/source.cram"
    assert "sha256" not in evidence["source"]  # No parent-source checksum campaign.
    assert identity["sha256"] == duplicate.sha256_file(receipt)


@pytest.mark.parametrize("damage", ["content", "header", "provenance", "flags", "counts", "missing_rg", "programs", "boolean_count"])
def test_binding_and_record_audit_fail_closed(vendor, damage):
    alignment, provenance, header, groups, entry, receipt = vendor
    if damage == "content":
        alignment.write_bytes(b"changed fixture of equal length!!")
    elif damage == "header":
        header = header.replace("SM:HG002", "SM:another")
    elif damage == "provenance":
        provenance.write_text("changed provenance")
    elif damage == "flags":
        entry["prepared_flags_sha256"] = "c" * 64
    elif damage == "counts":
        entry["prepared_read_groups"]["ug"]["duplicate_primary_records"] = 8
    elif damage == "missing_rg":
        entry["prepared_read_groups"] = {}
    elif damage == "programs":
        entry["vendor_program_ids"] = ["imaginary-program"]
    elif damage == "boolean_count":
        entry["prepared_read_groups"]["ug"]["primary_records"] = True
    with pytest.raises(ValueError):
        duplicate.validate_alignment(entry, alignment, header, groups)


def test_explicit_vendor_disable_fails_even_with_positive_duplicate_flags(vendor):
    alignment, provenance, header, groups, entry, receipt = vendor
    header = header.replace("demux --umi", "demux --mark-duplicates=false --umi")
    entry["alignment"]["header_sha256"] = hashlib.sha256(header.encode()).hexdigest()
    with pytest.raises(ValueError, match="disables duplicate"):
        duplicate.validate_alignment(entry, alignment, header, groups)


def test_zero_flags_require_actual_bound_producer_execution(vendor, tmp_path):
    alignment, provenance, header, groups, entry, receipt = vendor
    entry["selected_read_groups"]["ug"]["duplicate_primary_records"] = 0
    entry["prepared_read_groups"]["ug"]["duplicate_primary_records"] = 0
    with pytest.raises(ValueError, match="zero-duplicate native producer"):
        duplicate.validate_alignment(entry, alignment, header, groups)
    producer = tmp_path / "producer.json"
    source = {key: entry["source"][key] for key in ("s3_uri", "bytes", "header_sha256")}
    producer.write_text(json.dumps({"status": "completed", "source": source,
                                    "argv": ["demux", "--mark-duplicates=true"]}))
    entry["zero_duplicate_producer_receipt"] = {"path": str(producer), "sha256": duplicate.sha256_file(producer)}
    assert duplicate.validate_alignment(entry, alignment, header, groups)["observed_duplicate_primary_records"] == 0
    producer.write_text(json.dumps({"status": "completed", "source": source, "argv": ["demux"]}))
    entry["zero_duplicate_producer_receipt"]["sha256"] = duplicate.sha256_file(producer)
    with pytest.raises(ValueError, match="mark-duplicates=true"):
        duplicate.validate_alignment(entry, alignment, header, groups)
    producer.write_text(json.dumps({"status": "completed", "source": source,
                                    "argv": ["demux", "--mark-duplicates=true", "--mark-duplicates=false"]}))
    entry["zero_duplicate_producer_receipt"]["sha256"] = duplicate.sha256_file(producer)
    with pytest.raises(ValueError, match="mark-duplicates=true"):
        duplicate.validate_alignment(entry, alignment, header, groups)


def test_receipt_cannot_bind_unselected_or_repeated_alignment(vendor, tmp_path):
    alignment, provenance, header, groups, entry, receipt = vendor
    other = tmp_path / "other.cram"
    other.write_bytes(b"unselected")
    with pytest.raises(ValueError, match="identity differs"):
        duplicate.load_receipt(receipt, [other])


def test_native_profile_consumes_vendor_receipt_without_fabricating_pg(vendor, tmp_path, monkeypatch):
    alignment, provenance, header, groups, entry, receipt = vendor
    ont = tmp_path / "ont.cram"
    ont.write_bytes(b"ONT fixture")
    for path in (alignment, ont):
        (tmp_path / (path.name + ".crai")).write_bytes(b"index")
    pipeline = HybridPangenome()
    pipeline.experimental_ultima = True
    pipeline.output_vcf = tmp_path / "sample.vcf.gz"
    pipeline.reference = tmp_path / "reference.fa"
    pipeline.reference.write_text(">chr1\nA\n")
    pipeline.fai_data = {"chr1": {"length": 1000}}
    pipeline.sr_aln = [alignment]
    pipeline.lr_aln = [ont]
    pipeline.sr_duplicate_marking_receipt = receipt
    ont_header = header.replace("ID:ug\t", "ID:ont\t").replace("PL:ULTIMA", "PL:ONT")
    monkeypatch.setattr(ultima_pangenome.subprocess, "run", lambda command, **kwargs:
                        SimpleNamespace(stdout=header if command[-1] == str(alignment) else ont_header))
    profile = ultima_pangenome.UltimaProfile(pipeline)
    pipeline.ultima_profile = profile
    profile.start()
    profile.collect_readgroups()
    pipeline.validate_readgroups()
    assert pipeline.sample_sm == "HG002"
    assert profile.data["alignments"][0]["duplicate_marking_evidence"]["observed_duplicate_primary_records"] == 7
    assert profile.data["duplicate_marking_receipt"]["sha256"] == duplicate.sha256_file(receipt)
    assert "Dedup" not in header


def test_duplicate_receipt_requires_experimental_opt_in(vendor):
    pipeline = HybridPangenome()
    pipeline.sr_duplicate_marking_receipt = vendor[-1]
    with pytest.raises(ValueError, match="requires --experimental_ultima"):
        pipeline.validate()
