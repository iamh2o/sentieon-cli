#!/usr/bin/env python3
"""Compare two key-sorted canonical VCF TSV streams without loading them."""

from __future__ import annotations

import argparse
import collections
import gzip
import json
from pathlib import Path
from typing import Iterator, TextIO


FIELDS = (
    "key",
    "chrom",
    "pos",
    "ref",
    "alt",
    "gt",
    "qual",
    "filter",
    "lhc",
    "ml_prob",
    "info",
)


def open_text(path: Path, mode: str) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8", newline="")
    return path.open(mode, encoding="utf-8", newline="")


def read_groups(path: Path) -> Iterator[tuple[str, list[list[str]]]]:
    with open_text(path, "rt") as source:
        current_key: str | None = None
        rows: list[list[str]] = []
        for line_number, line in enumerate(source, 1):
            columns = line.rstrip("\n").split("\t", len(FIELDS) - 1)
            if len(columns) != len(FIELDS):
                raise ValueError(
                    f"{path}:{line_number}: expected {len(FIELDS)} columns, "
                    f"found {len(columns)}"
                )
            key = columns[0]
            if current_key is not None and key < current_key:
                raise ValueError(
                    f"{path}:{line_number}: input is not key-sorted"
                )
            if current_key is not None and key != current_key:
                yield current_key, rows
                rows = []
            current_key = key
            rows.append(columns)
        if current_key is not None:
            yield current_key, rows


def variant_type(row: list[str]) -> str:
    ref, alt = row[3], row[4]
    if alt.startswith("<") or "[" in alt or "]" in alt or alt == "*":
        return "symbolic"
    if len(ref) == 1 and len(alt) == 1:
        return "snv"
    if len(ref) == len(alt):
        return "mnv"
    return "indel"


def classify(left: list[str], right: list[str]) -> str:
    changes: list[str] = []
    if left[5] != right[5]:
        changes.append("genotype")
    if left[7] != right[7]:
        changes.append("filter")
    if left[6] != right[6]:
        changes.append("qual")
    if left[8] != right[8] or left[9] != right[9] or left[10] != right[10]:
        changes.append("annotation")
    return "+".join(changes) if changes else "identical"


def consume_identical(
    left: list[list[str]], right: list[list[str]]
) -> tuple[list[list[str]], list[list[str]], int]:
    right_counts = collections.Counter(tuple(row[1:]) for row in right)
    kept_left: list[list[str]] = []
    identical = 0
    for row in left:
        payload = tuple(row[1:])
        if right_counts[payload]:
            right_counts[payload] -= 1
            identical += 1
        else:
            kept_left.append(row)
    kept_right: list[list[str]] = []
    for row in right:
        payload = tuple(row[1:])
        if right_counts[payload]:
            right_counts[payload] -= 1
            kept_right.append(row)
    return kept_left, kept_right, identical


def emit(
    output: TextIO,
    status: str,
    left: list[str] | None,
    right: list[str] | None,
) -> None:
    row = left or right
    assert row is not None
    output.write(
        "\t".join(
            (
                status,
                row[0],
                row[1],
                row[2],
                row[3],
                row[4],
                variant_type(row),
                left[5] if left else ".",
                right[5] if right else ".",
                left[6] if left else ".",
                right[6] if right else ".",
                left[7] if left else ".",
                right[7] if right else ".",
                left[8] if left else ".",
                right[8] if right else ".",
                left[9] if left else ".",
                right[9] if right else ".",
                left[10] if left else ".",
                right[10] if right else ".",
            )
        )
    )
    output.write("\n")


def compare(left_path: Path, right_path: Path, output_path: Path) -> dict[str, int]:
    left_iter = iter(read_groups(left_path))
    right_iter = iter(read_groups(right_path))
    left_group = next(left_iter, None)
    right_group = next(right_iter, None)
    counts: collections.Counter[str] = collections.Counter()

    with open_text(output_path, "wt") as output:
        output.write(
            "\t".join(
                (
                    "status",
                    "key",
                    "chrom",
                    "pos",
                    "ref",
                    "alt",
                    "variant_type",
                    "derived_gt",
                    "native_gt",
                    "derived_qual",
                    "native_qual",
                    "derived_filter",
                    "native_filter",
                    "derived_lhc",
                    "native_lhc",
                    "derived_ml_prob",
                    "native_ml_prob",
                    "derived_info",
                    "native_info",
                )
            )
        )
        output.write("\n")

        while left_group is not None or right_group is not None:
            if right_group is None or (
                left_group is not None and left_group[0] < right_group[0]
            ):
                for row in left_group[1]:
                    emit(output, "derived_only", row, None)
                    counts["derived_only"] += 1
                left_group = next(left_iter, None)
                continue
            if left_group is None or right_group[0] < left_group[0]:
                for row in right_group[1]:
                    emit(output, "native_only", None, row)
                    counts["native_only"] += 1
                right_group = next(right_iter, None)
                continue

            left_rows, right_rows, identical = consume_identical(
                left_group[1], right_group[1]
            )
            counts["identical"] += identical
            paired = min(len(left_rows), len(right_rows))
            for index in range(paired):
                status = classify(left_rows[index], right_rows[index])
                emit(output, status, left_rows[index], right_rows[index])
                counts[status] += 1
            for row in left_rows[paired:]:
                emit(output, "derived_only", row, None)
                counts["derived_only"] += 1
            for row in right_rows[paired:]:
                emit(output, "native_only", None, row)
                counts["native_only"] += 1
            left_group = next(left_iter, None)
            right_group = next(right_iter, None)

    return dict(sorted(counts.items()))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--derived", required=True, type=Path)
    parser.add_argument("--native", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--summary", required=True, type=Path)
    args = parser.parse_args()

    counts = compare(args.derived, args.native, args.output)
    args.summary.write_text(
        json.dumps(counts, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
