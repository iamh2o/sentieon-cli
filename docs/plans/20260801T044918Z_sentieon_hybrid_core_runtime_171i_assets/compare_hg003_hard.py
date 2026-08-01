#!/usr/bin/env python
"""Compare matched direct Hybrid CLI outputs without loading them in memory."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import pathlib
import subprocess
import sys

VOLATILE_HEADER_PREFIXES = (b"##bcftools_",)
QUERY_REGIONS = ("chr1:1-1000000", "chr21:1-1000000", "chrX:1-1000000")


def summarize(path: pathlib.Path) -> dict[str, object]:
    header: list[str] = []
    body_hash = hashlib.sha256()
    records = 0
    with gzip.open(path, "rb") as stream:
        for line in stream:
            if line.startswith(b"#"):
                if not line.startswith(VOLATILE_HEADER_PREFIXES):
                    header.append(line.decode(errors="strict").rstrip("\n"))
                continue
            body_hash.update(line)
            records += 1
    tabix_contigs = subprocess.check_output(
        ["tabix", "-l", str(path)], text=True
    ).splitlines()
    queries = {
        region: hashlib.sha256(
            subprocess.check_output(["tabix", str(path), region])
        ).hexdigest()
        for region in QUERY_REGIONS
    }
    return {
        "path": str(path),
        "semantic_header": header,
        "body_sha256": body_hash.hexdigest(),
        "records": records,
        "tabix_contigs": tabix_contigs,
        "query_sha256": queries,
    }


def compare_file(
    baseline: pathlib.Path, optimized: pathlib.Path
) -> dict[str, object]:
    baseline_summary = summarize(baseline)
    optimized_summary = summarize(optimized)
    keys = (
        "semantic_header",
        "body_sha256",
        "records",
        "tabix_contigs",
        "query_sha256",
    )
    differences = [
        key for key in keys if baseline_summary[key] != optimized_summary[key]
    ]
    return {
        "baseline": baseline_summary,
        "optimized": optimized_summary,
        "differences": differences,
        "parity": not differences,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("baseline_dir", type=pathlib.Path)
    parser.add_argument("optimized_dir", type=pathlib.Path)
    parser.add_argument("output_json", type=pathlib.Path)
    args = parser.parse_args()
    baseline_files = sorted(args.baseline_dir.glob("*.vcf.gz"))
    optimized_files = sorted(args.optimized_dir.glob("*.vcf.gz"))
    baseline_names = [path.name for path in baseline_files]
    optimized_names = [path.name for path in optimized_files]
    if baseline_names != optimized_names or not baseline_names:
        raise RuntimeError(
            "baseline and optimized VCF file sets are absent or different"
        )
    comparison = {
        name: compare_file(
            args.baseline_dir / name,
            args.optimized_dir / name,
        )
        for name in baseline_names
    }
    result = {
        "all_parity": all(item["parity"] for item in comparison.values()),
        "files": comparison,
    }
    args.output_json.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if result["all_parity"] else 1


if __name__ == "__main__":
    sys.exit(main())
