"""Subset a VCF by a generated BED, including a valid empty interval set.

VariantPhaser may successfully emit no phased intervals.  bcftools rejects an
empty targets file, so that set selects a header-only VCF.  The complementary
unphased branch still processes its intervals; this does not classify a sample
as a negative control or turn a caller failure into a successful no-call.
"""

import argparse
import os
import pathlib
import sys
from typing import Optional, Sequence


def bed_has_intervals(path: pathlib.Path) -> bool:
    """Require a readable regular BED; leave nonempty BED parsing to bcftools."""
    if not path.is_file():
        raise ValueError(f"targets BED is not a regular file: {path}")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            content = line.strip()
            if content and not content.startswith("#"):
                return True
    return False


def main(argv: Optional[Sequence[str]] = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bed", type=pathlib.Path, required=True)
    parser.add_argument("--vcf", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    try:
        has_intervals = bed_has_intervals(args.bed)
    except (OSError, UnicodeError, ValueError) as exc:
        parser.exit(2, f"Cannot read targets BED: {exc}\n")

    if has_intervals:
        selection = ["-T", str(args.bed)]
    else:
        selection = ["--header-only"]
        print(
            f"No intervals in {args.bed}; selecting a header-only VCF subset",
            file=sys.stderr,
        )

    # Replacing this process preserves bcftools' exit status and pipe semantics.
    command = ["bcftools", "view", *selection, str(args.vcf)]
    try:
        os.execvp(command[0], command)
    except OSError as exc:
        parser.exit(2, f"Cannot execute bcftools: {exc}\n")


if __name__ == "__main__":
    main()
