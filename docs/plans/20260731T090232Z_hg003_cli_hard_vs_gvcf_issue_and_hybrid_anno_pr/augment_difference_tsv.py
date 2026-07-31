#!/usr/bin/env python3
"""Add source, category, population, and interpretation columns to VCF deltas."""

from __future__ import annotations

import argparse
import csv
import gzip
from pathlib import Path
from typing import TextIO


POPULATION_FIELDS = (
    "AC",
    "AF",
    "AN",
    "AC_genomes",
    "AF_genomes",
    "AN_genomes",
    "AC_v20",
    "AF_v20",
    "AN_v20",
)


def open_text(path: Path, mode: str) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8", newline="")
    return path.open(mode, encoding="utf-8", newline="")


def parse_info(value: str) -> dict[str, str]:
    parsed: dict[str, str] = {}
    if value in ("", "."):
        return parsed
    for field in value.split(";"):
        if "=" in field:
            key, item = field.split("=", 1)
            parsed[key] = item
        elif field:
            parsed[field] = "true"
    return parsed


def interpretation(row: dict[str, str]) -> str:
    status = row["status"]
    if status in ("derived_only", "native_only"):
        return "presence_absence"
    changes = set(status.split("+"))
    if "genotype" in changes:
        return "genotype"
    if "filter" in changes:
        filters = {row["derived_filter"], row["native_filter"]}
        if "MLrejected" in filters:
            return "modelapply_filtering"
        return "other_filtering"
    if changes == {"annotation"}:
        return "annotation_only"
    if changes == {"qual"}:
        return "quality_only"
    if changes <= {"annotation", "qual"}:
        return "annotation_or_quality"
    if status == "identical":
        return "identical"
    return status


def augment(
    input_path: Path,
    output_path: Path,
    category: str,
) -> None:
    if category in {"tp-baseline", "fn"}:
        derived_lane = "giab-hg003-v4.2.1-derived-evaluation"
        native_lane = "giab-hg003-v4.2.1-native-evaluation"
    else:
        derived_lane = "gvcftyper-derived-hard"
        native_lane = "native-cli-hard"

    with open_text(input_path, "rt") as source, open_text(
        output_path, "wt"
    ) as output:
        reader = csv.DictReader(source, delimiter="\t")
        if reader.fieldnames is None:
            raise ValueError(f"{input_path} has no header")
        required = {
            "status",
            "derived_gt",
            "native_gt",
            "derived_filter",
            "native_filter",
            "derived_info",
            "native_info",
        }
        missing = required.difference(reader.fieldnames)
        if missing:
            raise ValueError(
                f"{input_path} is missing required columns: {sorted(missing)}"
            )
        extra = [
            "rtg_category",
            "interpretation",
            "derived_source_lane",
            "native_source_lane",
        ]
        for side in ("derived", "native"):
            extra.extend(f"{side}_{field}" for field in POPULATION_FIELDS)
        writer = csv.DictWriter(
            output,
            fieldnames=[*reader.fieldnames, *extra],
            delimiter="\t",
            lineterminator="\n",
        )
        writer.writeheader()
        for row in reader:
            derived_present = row["status"] != "native_only"
            native_present = row["status"] != "derived_only"
            row["rtg_category"] = category
            row["interpretation"] = interpretation(row)
            row["derived_source_lane"] = (
                derived_lane if derived_present else "."
            )
            row["native_source_lane"] = (
                native_lane if native_present else "."
            )
            for side in ("derived", "native"):
                info = parse_info(row[f"{side}_info"])
                for field in POPULATION_FIELDS:
                    row[f"{side}_{field}"] = info.get(field, ".")
            writer.writerow(row)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--category", required=True)
    args = parser.parse_args()
    augment(args.input, args.output, args.category)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
