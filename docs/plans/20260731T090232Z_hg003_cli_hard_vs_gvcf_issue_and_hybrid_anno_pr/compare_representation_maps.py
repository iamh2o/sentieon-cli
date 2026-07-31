#!/usr/bin/env python3
"""Find raw representations that collapse to identical normalized alleles."""

from __future__ import annotations

import argparse
import collections
import csv
import gzip
import json
from pathlib import Path
from typing import Iterator, TextIO


FIELDS = (
    "normalized_key",
    "raw_key",
    "chrom",
    "pos",
    "ref",
    "alt",
    "gt",
    "qual",
    "filter",
    "info",
)


def open_text(path: Path, mode: str) -> TextIO:
    if path.suffix == ".gz":
        return gzip.open(path, mode, encoding="utf-8", newline="")
    return path.open(mode, encoding="utf-8", newline="")


def groups(path: Path) -> Iterator[tuple[str, list[dict[str, str]]]]:
    with open_text(path, "rt") as source:
        reader = csv.DictReader(source, fieldnames=FIELDS, delimiter="\t")
        current_key: str | None = None
        rows: list[dict[str, str]] = []
        for line_number, row in enumerate(reader, 1):
            key = row["normalized_key"]
            if row["raw_key"] in ("", "."):
                row["raw_key"] = key
            if current_key is not None and key < current_key:
                raise ValueError(f"{path}:{line_number}: input is not sorted")
            if current_key is not None and key != current_key:
                yield current_key, rows
                rows = []
            current_key = key
            rows.append(row)
        if current_key is not None:
            yield current_key, rows


def payload(row: dict[str, str]) -> tuple[str, ...]:
    info = ";".join(
        item
        for item in row["info"].split(";")
        if not item.startswith("ORIG=")
    )
    return row["gt"], row["qual"], row["filter"], info


def compare(
    derived_path: Path,
    native_path: Path,
    output_path: Path,
) -> dict[str, int]:
    derived_iter = iter(groups(derived_path))
    native_iter = iter(groups(native_path))
    derived_group = next(derived_iter, None)
    native_group = next(native_iter, None)
    counts: collections.Counter[str] = collections.Counter()

    with open_text(output_path, "wt") as output:
        writer = csv.writer(output, delimiter="\t", lineterminator="\n")
        writer.writerow(
            (
                "normalized_key",
                "chrom",
                "pos",
                "ref",
                "alt",
                "derived_raw_key",
                "native_raw_key",
                "gt",
                "qual",
                "filter",
                "info",
                "classification",
            )
        )
        while derived_group is not None and native_group is not None:
            if derived_group[0] < native_group[0]:
                derived_group = next(derived_iter, None)
                continue
            if native_group[0] < derived_group[0]:
                native_group = next(native_iter, None)
                continue

            derived_by_payload: dict[
                tuple[str, ...], list[dict[str, str]]
            ] = collections.defaultdict(list)
            native_by_payload: dict[
                tuple[str, ...], list[dict[str, str]]
            ] = collections.defaultdict(list)
            for row in derived_group[1]:
                derived_by_payload[payload(row)].append(row)
            for row in native_group[1]:
                native_by_payload[payload(row)].append(row)
            for item_payload, derived_rows in derived_by_payload.items():
                native_rows = native_by_payload.get(item_payload, [])
                used: set[int] = set()
                unmatched_derived: list[dict[str, str]] = []
                for derived in derived_rows:
                    exact_index = next(
                        (
                            index
                            for index, native in enumerate(native_rows)
                            if index not in used
                            and native["raw_key"] == derived["raw_key"]
                        ),
                        None,
                    )
                    if exact_index is None:
                        unmatched_derived.append(derived)
                    else:
                        used.add(exact_index)
                unmatched_native = [
                    native
                    for index, native in enumerate(native_rows)
                    if index not in used
                ]
                for derived, native in zip(
                    unmatched_derived, unmatched_native, strict=False
                ):
                    writer.writerow(
                        (
                            derived["normalized_key"],
                            derived["chrom"],
                            derived["pos"],
                            derived["ref"],
                            derived["alt"],
                            derived["raw_key"],
                            native["raw_key"],
                            derived["gt"],
                            derived["qual"],
                            derived["filter"],
                            payload(derived)[3],
                            "representation_or_multiallelic_decomposition",
                        )
                    )
                    counts["representation_or_multiallelic_decomposition"] += 1
            derived_group = next(derived_iter, None)
            native_group = next(native_iter, None)
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
