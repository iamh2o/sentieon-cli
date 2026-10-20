"""Validate explicit vendor Ultima duplicate evidence bound to prepared bytes.

This consumes a completed preparation receipt. It does not infer vendor tool
defaults, fabricate @PG lines, re-mark duplicates, or hash the parent source.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from typing import Any

SCHEMA = "sentieon.ultima_duplicate_marking.v1"
VENDOR_DOCUMENTATION = "https://github.com/Ultimagen/healthomics-workflows/blob/main/workflows/trim_align_sort/howto-ua-align-sort.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _sha(value: Any, field: str) -> str:
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError(f"Invalid SHA256 for duplicate receipt {field}")
    return value


def _integer(value: Any, field: str, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        raise ValueError(f"Invalid integer for duplicate receipt {field}")
    return value


def _bound_file(spec: Any, field: str) -> dict[str, Any]:
    if not isinstance(spec, dict) or not isinstance(spec.get("path"), str):
        raise ValueError(f"Missing bound file for duplicate receipt {field}")
    path = Path(spec["path"])
    if not path.is_absolute() or not path.is_file():
        raise ValueError(f"Expected absolute existing file for {field}: {path}")
    expected = _sha(spec.get("sha256"), field)
    if sha256_file(path) != expected:
        raise ValueError(f"Duplicate receipt bound file SHA256 differs: {field}")
    return {"path": str(path.resolve()), "sha256": expected}


def load_receipt(path: Path, alignments: list[Path]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Require one explicit prepared-output entry per selected Ultima input."""
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict) or payload.get("schema") != SCHEMA or payload.get("status") != "completed":
        raise ValueError("Expected completed typed Ultima duplicate-marking receipt")
    entries = payload.get("alignments")
    if not isinstance(entries, list) or len(entries) != len(alignments):
        raise ValueError("Duplicate receipt must bind every selected Ultima alignment")
    bound = {}
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("alignment"), dict):
            raise ValueError("Malformed duplicate receipt alignment entry")
        selected = entry["alignment"].get("path")
        if not isinstance(selected, str) or not Path(selected).is_absolute():
            raise ValueError("Duplicate receipt alignment path must be absolute")
        key = str(Path(selected).resolve())
        if key in bound:
            raise ValueError("Duplicate receipt contains a repeated alignment")
        bound[key] = entry
    if set(bound) != {str(item.resolve()) for item in alignments}:
        raise ValueError("Duplicate receipt alignment identity differs from --sr_aln")
    identity = {"path": str(path.resolve()), "bytes": path.stat().st_size,
                "sha256": sha256_file(path), "schema": SCHEMA}
    return bound, identity


def _counts(value: Any, rg_ids: set[str], field: str) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != rg_ids:
        raise ValueError(f"Duplicate receipt {field} must cover every actual read group")
    for rg_id, row in value.items():
        if not isinstance(row, dict) or set(row) != {"primary_records", "duplicate_primary_records"}:
            raise ValueError(f"Malformed duplicate counts for {field}.{rg_id}")
        primary = _integer(row["primary_records"], f"{field}.{rg_id}.primary_records")
        duplicate = _integer(row["duplicate_primary_records"], f"{field}.{rg_id}.duplicate_primary_records")
        if duplicate > primary:
            raise ValueError("Duplicate primary count exceeds primary count")
    if sum(row["primary_records"] for row in value.values()) == 0:
        raise ValueError("Duplicate receipt has no primary records")
    return value


def validate_alignment(entry: dict[str, Any], path: Path, header: str,
                       groups: list[dict[str, str]]) -> dict[str, Any]:
    """Verify receipt bytes/header and require native duplicate-state evidence."""
    prepared = entry["alignment"]
    if _integer(prepared.get("bytes"), "alignment.bytes", 1) != path.stat().st_size:
        raise ValueError("Duplicate receipt prepared alignment size differs")
    _bound_file(prepared, "prepared alignment")
    header_sha = hashlib.sha256(header.encode()).hexdigest()
    if _sha(prepared.get("header_sha256"), "alignment.header_sha256") != header_sha:
        raise ValueError("Duplicate receipt prepared alignment header differs")
    source = entry.get("source")
    if not isinstance(source, dict) or not isinstance(source.get("s3_uri"), str) or not re.fullmatch(r"s3://[a-z0-9.-]+/[^\s?#]+", source["s3_uri"]):
        raise ValueError("Duplicate receipt requires an exact source S3 URI")
    _integer(source.get("bytes"), "source.bytes", 1)
    _sha(source.get("header_sha256"), "source.header_sha256")
    if "sha256" in source:
        _sha(source["sha256"], "accepted source SHA256")
    accepted = _bound_file({"path": source.get("accepted_provenance_path"),
                           "sha256": source.get("accepted_provenance_sha256")}, "accepted source provenance")
    programs = {}
    for line in header.splitlines():
        if line.startswith("@PG\t"):
            values = dict(field.split(":", 1) for field in line.split("\t")[1:])
            if not values.get("ID") or values["ID"] in programs:
                raise ValueError("Vendor duplicate receipt header has a missing or repeated @PG ID")
            programs[values["ID"]] = values
            if re.search(r"(?:^|\s)--mark-duplicates(?:=|\s+)(?:false|0)(?:\s|\"|$)", values.get("CL", ""), re.IGNORECASE):
                raise ValueError("Vendor header explicitly disables duplicate marking")
    ids = entry.get("vendor_program_ids")
    actual_ids = {key for key, value in programs.items() if value.get("PN", "").lower() in ("demux", "sorter")}
    if (not isinstance(ids, list) or any(not isinstance(item, str) for item in ids)
            or len(set(ids)) != len(ids) or set(ids) != actual_ids
            or {programs[key].get("PN", "").lower() for key in actual_ids} != {"demux", "sorter"}
            or any(not programs[key].get("VN") for key in actual_ids)):
        raise ValueError("Duplicate receipt must identify the actual vendor demux and sorter programs")
    if entry.get("state") != "marked" or entry.get("flags_preserved") is not True:
        raise ValueError("Duplicate receipt must preserve the marked duplicate state")
    selected_sha = _sha(entry.get("selected_flags_sha256"), "selected_flags_sha256")
    if selected_sha != _sha(entry.get("prepared_flags_sha256"), "prepared_flags_sha256"):
        raise ValueError("Selected and prepared duplicate flag streams differ")
    rg_ids = {group["ID"] for group in groups}
    selected = _counts(entry.get("selected_read_groups"), rg_ids, "selected_read_groups")
    prepared_counts = _counts(entry.get("prepared_read_groups"), rg_ids, "prepared_read_groups")
    if selected != prepared_counts:
        raise ValueError("Selected and prepared duplicate read-group counts differ")
    duplicates = sum(row["duplicate_primary_records"] for row in selected.values())
    producer_identity = None
    if duplicates == 0:
        # Zero flags alone cannot establish that marking occurred. Require an
        # actual bound producer execution receipt with the explicit option.
        producer_identity = _bound_file(entry.get("zero_duplicate_producer_receipt"), "zero-duplicate native producer")
        producer = json.loads(Path(producer_identity["path"]).read_text())
        if not isinstance(producer, dict):
            raise ValueError("Zero-duplicate native producer receipt must be an object")
        argv = producer.get("argv")
        enabled = False
        if isinstance(argv, list) and argv and all(isinstance(x, str) for x in argv):
            choices = [arg.split("=", 1)[1] for arg in argv if arg.startswith("--mark-duplicates=")]
            choices.extend(argv[i + 1] for i, arg in enumerate(argv[:-1]) if arg == "--mark-duplicates")
            enabled = Path(argv[0]).name == "demux" and choices == ["true"]
        binding = {key: source[key] for key in ("s3_uri", "bytes", "header_sha256")}
        if producer.get("status") != "completed" or producer.get("source") != binding or not enabled:
            raise ValueError("Zero duplicate count requires bound native producer mark-duplicates=true evidence")
    return {"kind": "bound vendor duplicate-marking preparation receipt",
            "prepared_alignment_sha256": prepared["sha256"], "header_sha256": header_sha,
            "source": source, "accepted_provenance": accepted,
            "vendor_program_ids": ids, "vendor_documentation": VENDOR_DOCUMENTATION,
            "flag_stream_sha256": selected_sha, "read_group_counts": selected,
            "observed_duplicate_primary_records": duplicates,
            "zero_duplicate_producer_receipt": producer_identity,
            "audit_authority": "Completed preparation's independently decoded record audit; parent source not rehashed"}
