#!/usr/bin/env python
"""Selective, order-preserving final normalization for Hybrid VCFs."""

from __future__ import annotations

import argparse
import bisect
import multiprocessing as mp
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import BinaryIO, Iterator, Sequence, cast

from vcflib import bgzf

MARKER = b"SENTIEON_HYBRID_NORM_ORDINAL"
MARKER_HEADER = (
    b"##INFO=<ID=SENTIEON_HYBRID_NORM_ORDINAL,Number=1,Type=Integer,"
    b'Description="Temporary Hybrid normalization stream ordinal">\n'
)
DEFAULT_BATCH_CANDIDATES = 8_192
DEFAULT_BATCH_BYTES = 256 * 1024 * 1024
REFERENCE_CHUNK_BASES = 4 * 1024 * 1024


class HybridNormError(RuntimeError):
    """A selective-normalization contract or subprocess failed."""


@dataclass(frozen=True)
class FaiEntry:
    """Fields required to address one FASTA contig."""

    length: int
    offset: int
    line_bases: int
    line_width: int


def run_checked(
    command: Sequence[str],
    label: str,
    input_bytes: bytes | None = None,
) -> bytes:
    """Run a bounded helper command and return its stdout."""

    try:
        result = subprocess.run(
            command,
            input=input_bytes,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
    except FileNotFoundError as error:
        raise HybridNormError(
            f"required executable {command[0]} is missing"
        ) from error
    if result.returncode != 0:
        message = result.stderr.decode(errors="replace").strip()
        raise HybridNormError(
            f"{label} failed with exit code {result.returncode}: {message}"
        )
    return result.stdout


def load_fai(path: pathlib.Path) -> dict[str, FaiEntry]:
    """Load a complete FASTA index and reject ambiguous entries."""

    if not path.is_file():
        raise HybridNormError(f"reference index {path} does not exist")
    entries: dict[str, FaiEntry] = {}
    with path.open() as reference_index:
        for line_number, line in enumerate(reference_index, 1):
            columns = line.rstrip().split("\t")
            if len(columns) != 5:
                raise HybridNormError(
                    f"reference index line {line_number} does not have "
                    "five fields"
                )
            contig = columns[0]
            try:
                length, offset, line_bases, line_width = (
                    int(value) for value in columns[1:]
                )
            except ValueError as error:
                raise HybridNormError(
                    f"reference index line {line_number} has a "
                    "non-integer field"
                ) from error
            if contig in entries:
                raise HybridNormError(
                    f"reference index contains duplicate contig {contig}"
                )
            if (
                length <= 0
                or offset < 0
                or line_bases <= 0
                or line_width < line_bases
            ):
                raise HybridNormError(
                    f"reference index line {line_number} has invalid "
                    "dimensions"
                )
            entries[contig] = FaiEntry(
                length=length,
                offset=offset,
                line_bases=line_bases,
                line_width=line_width,
            )
    if not entries:
        raise HybridNormError("reference index declares no contigs")
    return entries


def scan_bgzf_blocks(path: pathlib.Path) -> tuple[list[int], list[int]]:
    """Map uncompressed byte offsets to BGZF block offsets."""

    uncompressed_offsets: list[int] = []
    compressed_offsets: list[int] = []
    compressed_offset = 0
    uncompressed_offset = 0
    file_size = path.stat().st_size
    with path.open("rb") as input_file:
        while compressed_offset < file_size:
            input_file.seek(compressed_offset)
            fixed_header = input_file.read(12)
            if len(fixed_header) != 12:
                raise HybridNormError("truncated BGZF fixed header")
            if fixed_header[:3] != b"\x1f\x8b\x08":
                raise HybridNormError("reference is gzip data but not BGZF")
            flags = fixed_header[3]
            if not flags & 4:
                raise HybridNormError("reference is gzip data but not BGZF")
            extra_length = struct.unpack("<H", fixed_header[10:12])[0]
            extra = input_file.read(extra_length)
            if len(extra) != extra_length:
                raise HybridNormError("truncated BGZF extra header")

            block_size: int | None = None
            offset = 0
            while offset + 4 <= len(extra):
                subfield_id = extra[offset : offset + 2]
                subfield_length = struct.unpack(
                    "<H", extra[offset + 2 : offset + 4]
                )[0]
                value_start = offset + 4
                value_end = value_start + subfield_length
                if value_end > len(extra):
                    raise HybridNormError("malformed BGZF extra header")
                if subfield_id == b"BC" and subfield_length == 2:
                    block_size = (
                        struct.unpack("<H", extra[value_start:value_end])[0]
                        + 1
                    )
                offset = value_end
            if block_size is None:
                raise HybridNormError("reference is gzip data but not BGZF")
            if compressed_offset + block_size > file_size:
                raise HybridNormError("truncated BGZF block")

            input_file.seek(compressed_offset + block_size - 4)
            uncompressed_size_bytes = input_file.read(4)
            if len(uncompressed_size_bytes) != 4:
                raise HybridNormError("truncated BGZF block trailer")
            uncompressed_size = struct.unpack("<I", uncompressed_size_bytes)[0]
            if uncompressed_size:
                uncompressed_offsets.append(uncompressed_offset)
                compressed_offsets.append(compressed_offset)
                uncompressed_offset += uncompressed_size
            compressed_offset += block_size
    if compressed_offset != file_size or not uncompressed_offsets:
        raise HybridNormError("reference contains no readable BGZF blocks")
    return uncompressed_offsets, compressed_offsets


class ReferenceReader:
    """Bounded random FASTA access for plain or BGZF references."""

    def __init__(self, reference: pathlib.Path, fai: pathlib.Path) -> None:
        if not reference.is_file():
            raise HybridNormError(f"reference {reference} does not exist")
        self.entries = load_fai(fai)
        with reference.open("rb") as input_file:
            magic = input_file.read(2)
        self.compressed = magic == b"\x1f\x8b"
        self.uncompressed_offsets: list[int] = []
        self.compressed_offsets: list[int] = []
        if self.compressed:
            (
                self.uncompressed_offsets,
                self.compressed_offsets,
            ) = scan_bgzf_blocks(reference)
            self.handle: BinaryIO = bgzf.open(str(reference), "rb")
        else:
            self.handle = reference.open("rb")
        self.cache_contig: str | None = None
        self.cache_start = 0
        self.cache_sequence = b""

    def close(self) -> None:
        self.handle.close()

    def __enter__(self) -> ReferenceReader:
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def seek_uncompressed(self, offset: int) -> None:
        if not self.compressed:
            self.handle.seek(offset)
            return
        block_index = (
            bisect.bisect_right(self.uncompressed_offsets, offset) - 1
        )
        if block_index < 0:
            raise HybridNormError("FASTA offset precedes the first BGZF block")
        in_block_offset = offset - self.uncompressed_offsets[block_index]
        if in_block_offset > 0xFFFF:
            raise HybridNormError("FASTA offset exceeds a BGZF block")
        virtual_offset = (
            self.compressed_offsets[block_index] << 16
        ) | in_block_offset
        self.handle.seek(virtual_offset)

    def load_chunk(self, contig: str, position: int) -> None:
        try:
            entry = self.entries[contig]
        except KeyError as error:
            raise HybridNormError(
                f"VCF contig {contig} is absent from the reference index"
            ) from error
        if position < 0 or position >= entry.length:
            raise HybridNormError(
                f"VCF position {contig}:{position + 1} is outside the "
                "reference"
            )
        chunk_start = (
            position // REFERENCE_CHUNK_BASES
        ) * REFERENCE_CHUNK_BASES
        chunk_length = min(
            REFERENCE_CHUNK_BASES,
            entry.length - chunk_start,
        )
        raw_offset = (
            entry.offset
            + (chunk_start // entry.line_bases) * entry.line_width
            + chunk_start % entry.line_bases
        )
        line_offset = chunk_start % entry.line_bases
        line_break_width = entry.line_width - entry.line_bases
        line_breaks = (
            line_offset + chunk_length + entry.line_bases - 1
        ) // entry.line_bases
        raw_length = chunk_length + line_breaks * line_break_width + 8
        self.seek_uncompressed(raw_offset)
        raw = self.handle.read(raw_length)
        sequence = raw.replace(b"\n", b"").replace(b"\r", b"")
        if len(sequence) < chunk_length:
            raise HybridNormError(
                f"reference sequence for {contig} is shorter than its "
                "FAI entry"
            )
        self.cache_contig = contig
        self.cache_start = chunk_start
        self.cache_sequence = sequence[:chunk_length].upper()

    def base(self, contig: str, position: int) -> bytes:
        if not (
            self.cache_contig == contig
            and self.cache_start <= position
            and position < self.cache_start + len(self.cache_sequence)
        ):
            self.load_chunk(contig, position)
        return self.cache_sequence[position - self.cache_start :][0:1]


def parse_record(line: bytes) -> tuple[list[bytes], str, int, bytes, bytes]:
    """Parse fields needed for candidate selection and reference checking."""

    columns = line.rstrip().split(b"\t")
    if len(columns) < 8:
        raise HybridNormError(
            f"VCF record has fewer than eight columns: {line.rstrip()!r}"
        )
    try:
        contig = columns[0].decode()
        position = int(columns[1]) - 1
    except (UnicodeDecodeError, ValueError) as error:
        raise HybridNormError(
            f"invalid VCF record: {line.rstrip()!r}"
        ) from error
    if position < 0 or not columns[3]:
        raise HybridNormError(f"invalid VCF record: {line.rstrip()!r}")
    return columns, contig, position, columns[3], columns[4]


def needs_normalization(reference: bytes, alternate: bytes) -> bool:
    """Return whether ``bcftools norm`` can change representation."""

    if len(reference) != 1 or reference not in b"ACGT":
        return True
    if alternate == b".":
        return False
    for allele in alternate.split(b","):
        if allele == b"<NON_REF>":
            continue
        if len(allele) != 1 or allele not in b"ACGTN":
            return True
        if allele == reference:
            return True
    return False


def validate_reference(
    reader: ReferenceReader,
    contig: str,
    position: int,
    reference: bytes,
) -> None:
    """Reproduce the REF mismatch failure for safe pass-through records."""

    observed = reader.base(contig, position)
    if observed != reference.upper():
        raise HybridNormError(
            f"reference mismatch at {contig}:{position + 1}: "
            f"VCF REF={reference.decode(errors='replace')} "
            f"FASTA={observed.decode(errors='replace')}"
        )


def add_marker(line: bytes, ordinal: int) -> bytes:
    """Attach the temporary ordinal to one candidate INFO field."""

    columns = line.rstrip().split(b"\t")
    marker = MARKER + b"=" + str(ordinal).encode()
    columns[7] = marker if columns[7] == b"." else columns[7] + b";" + marker
    return b"\t".join(columns) + b"\n"


def strip_marker(line: bytes) -> tuple[int, bytes]:
    """Remove and return the temporary ordinal from normalized output."""

    columns = line.rstrip().split(b"\t")
    if len(columns) < 8:
        raise HybridNormError("normalized record has fewer than eight columns")
    prefix = MARKER + b"="
    ordinals: list[int] = []
    retained: list[bytes] = []
    for item in columns[7].split(b";"):
        if item.startswith(prefix):
            try:
                ordinals.append(int(item[len(prefix) :]))
            except ValueError as error:
                raise HybridNormError(
                    f"invalid temporary normalization ordinal: {item!r}"
                ) from error
        else:
            retained.append(item)
    if len(ordinals) != 1:
        raise HybridNormError(
            "normalized record does not contain exactly one temporary ordinal"
        )
    columns[7] = b";".join(retained) if retained else b"."
    return ordinals[0], b"\t".join(columns) + b"\n"


def add_marker_header(header: bytes) -> bytes:
    """Insert the marker declaration immediately before #CHROM."""

    if b"ID=" + MARKER + b"," in header:
        raise HybridNormError(
            f"input VCF already declares reserved INFO/{MARKER.decode()}"
        )
    column_offset = header.find(b"#CHROM\t")
    if column_offset < 0:
        raise HybridNormError("VCF header has no #CHROM line")
    return header[:column_offset] + MARKER_HEADER + header[column_offset:]


def normalized_header(header: bytes, reference: pathlib.Path) -> bytes:
    """Generate the same semantic header added by ``bcftools norm``."""

    output = run_checked(
        ["bcftools", "norm", "-f", str(reference)],
        "normalization header construction",
        input_bytes=header,
    )
    if any(not line.startswith(b"#") for line in output.splitlines()):
        raise HybridNormError("normalization header probe emitted record data")
    if not output.endswith(b"\n"):
        raise HybridNormError("normalization header is not newline terminated")
    return output


class Batch:
    """A bounded stream layout plus its selective candidate VCF."""

    def __init__(
        self,
        temp_dir: pathlib.Path,
        number: int,
        candidate_header: bytes,
    ) -> None:
        self.number = number
        self.layout_path = temp_dir / f"batch.{number:08d}.layout"
        self.candidate_path = temp_dir / f"batch.{number:08d}.candidates.vcf"
        self.normalized_path = temp_dir / f"batch.{number:08d}.normalized.vcf"
        self.layout = self.layout_path.open("wb")
        self.candidates = self.candidate_path.open("wb")
        self.candidates.write(candidate_header)
        self.records = 0
        self.candidate_count = 0
        self.layout_bytes = 0
        self.ordinals: set[int] = set()

    def add_passthrough(self, line: bytes) -> None:
        self.layout.write(b"R" + line)
        self.records += 1
        self.layout_bytes += len(line) + 1

    def add_candidate(self, line: bytes, ordinal: int) -> None:
        self.candidates.write(add_marker(line, ordinal))
        placeholder = b"C" + str(ordinal).encode() + b"\n"
        self.layout.write(placeholder)
        self.records += 1
        self.candidate_count += 1
        self.layout_bytes += len(placeholder)
        self.ordinals.add(ordinal)

    def full(self, candidate_limit: int, byte_limit: int) -> bool:
        return (
            self.candidate_count >= candidate_limit
            or self.layout_bytes >= byte_limit
        )

    def close(self) -> None:
        self.layout.close()
        self.candidates.close()

    def normalize(self, reference: pathlib.Path) -> dict[int, list[bytes]]:
        normalized: dict[int, list[bytes]] = {}
        if not self.candidate_count:
            return normalized
        result = subprocess.run(
            [
                "bcftools",
                "norm",
                "--no-version",
                "-f",
                str(reference),
                "-o",
                str(self.normalized_path),
                str(self.candidate_path),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if result.returncode != 0:
            message = result.stderr.decode(errors="replace").strip()
            raise HybridNormError(
                f"normalization batch {self.number} failed with exit code "
                f"{result.returncode}: {message}"
            )
        with self.normalized_path.open("rb") as normalized_vcf:
            for line in normalized_vcf:
                if line.startswith(b"#"):
                    continue
                ordinal, stripped = strip_marker(line)
                if ordinal not in self.ordinals:
                    raise HybridNormError(
                        f"normalization emitted unknown ordinal {ordinal}"
                    )
                normalized.setdefault(ordinal, []).append(stripped)
        return normalized

    def replay(
        self,
        output: BinaryIO,
        normalized: dict[int, list[bytes]],
    ) -> int:
        emitted = 0
        with self.layout_path.open("rb") as layout:
            for line in layout:
                if line.startswith(b"R"):
                    output.write(line[1:])
                    emitted += 1
                elif line.startswith(b"C"):
                    try:
                        ordinal = int(line[1:])
                    except ValueError as error:
                        raise HybridNormError(
                            f"invalid batch placeholder: {line!r}"
                        ) from error
                    records = normalized.pop(ordinal, [])
                    for record in records:
                        output.write(record)
                        emitted += 1
                else:
                    raise HybridNormError(
                        f"invalid batch layout entry: {line!r}"
                    )
        if normalized:
            raise HybridNormError(
                "normalized records were not restored to the stream"
            )
        return emitted

    def remove(self) -> None:
        for path in (
            self.layout_path,
            self.candidate_path,
            self.normalized_path,
        ):
            if path.exists():
                path.unlink()


def read_header_and_records(stream: BinaryIO) -> tuple[bytes, Iterator[bytes]]:
    """Read a VCF header and expose the remaining record iterator."""

    header_lines: list[bytes] = []
    first_record: bytes | None = None
    for line in stream:
        if line.startswith(b"#"):
            header_lines.append(line)
            continue
        first_record = line
        break
    header = b"".join(header_lines)
    if not header or b"#CHROM\t" not in header:
        raise HybridNormError(
            "bcftools view output has no complete VCF header"
        )

    def records() -> Iterator[bytes]:
        if first_record is not None:
            yield first_record
        yield from stream

    return header, records()


def partial_paths(
    output_path: pathlib.Path,
) -> tuple[pathlib.Path, pathlib.Path]:
    """Allocate a unique same-filesystem BGZF path."""

    descriptor, partial_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.partial.",
        suffix=".vcf.gz",
        dir=output_path.parent,
    )
    os.close(descriptor)
    partial = pathlib.Path(partial_name)
    return partial, pathlib.Path(f"{partial}.tbi")


def publish_pair(
    partial: pathlib.Path,
    partial_index: pathlib.Path,
    output: pathlib.Path,
) -> None:
    """Publish a completed pair and roll back ordinary rename failures."""

    if not partial.is_file() or not partial_index.is_file():
        raise HybridNormError("BGZF/index publication pair is incomplete")
    output_index = pathlib.Path(f"{output}.tbi")
    backup_vcf = pathlib.Path(f"{partial}.previous-vcf")
    backup_index = pathlib.Path(f"{partial}.previous-index")
    had_vcf = output.exists()
    had_index = output_index.exists()
    try:
        if had_vcf:
            os.replace(output, backup_vcf)
        if had_index:
            os.replace(output_index, backup_index)
        os.replace(partial, output)
        os.replace(partial_index, output_index)
    except BaseException:
        if output.exists():
            output.unlink()
        if output_index.exists():
            output_index.unlink()
        if had_vcf and backup_vcf.exists():
            os.replace(backup_vcf, output)
        if had_index and backup_index.exists():
            os.replace(backup_index, output_index)
        raise
    finally:
        if backup_vcf.exists():
            backup_vcf.unlink()
        if backup_index.exists():
            backup_index.unlink()


def process_records(
    records: Iterator[bytes],
    output: BinaryIO,
    reference: pathlib.Path,
    reference_reader: ReferenceReader,
    candidate_header: bytes,
    temp_dir: pathlib.Path,
    candidate_limit: int,
    byte_limit: int,
) -> tuple[int, int, int, int]:
    """Select, normalize, and replay bounded ordered batches."""

    input_records = 0
    candidates = 0
    output_records = 0
    batch_count = 0
    ordinal = 0
    batch = Batch(temp_dir, batch_count, candidate_header)
    try:
        for line in records:
            input_records += 1
            columns, contig, position, ref, alt = parse_record(line)
            if needs_normalization(ref, alt):
                batch.add_candidate(line, ordinal)
                candidates += 1
                ordinal += 1
            else:
                validate_reference(reference_reader, contig, position, ref)
                batch.add_passthrough(line)

            if batch.full(candidate_limit, byte_limit):
                batch.close()
                normalized = batch.normalize(reference)
                output_records += batch.replay(output, normalized)
                batch.remove()
                batch_count += 1
                batch = Batch(temp_dir, batch_count, candidate_header)

        if batch.records:
            batch.close()
            normalized = batch.normalize(reference)
            output_records += batch.replay(output, normalized)
            batch.remove()
            batch_count += 1
        else:
            batch.close()
            batch.remove()
    except BaseException:
        try:
            batch.close()
        except ValueError:
            pass
        raise
    return input_records, candidates, output_records, batch_count


def run_normalization(args: argparse.Namespace) -> int:
    """Execute selective normalization without touching target on failure."""

    if args.threads < 1:
        raise HybridNormError("--threads must be at least 1")
    if args.batch_candidates < 1:
        raise HybridNormError("--batch-candidates must be at least 1")
    if args.batch_bytes < 1:
        raise HybridNormError("--batch-bytes must be at least 1")

    input_vcf = pathlib.Path(args.input_vcf).resolve()
    reference = pathlib.Path(args.reference).resolve()
    reference_fai = pathlib.Path(f"{reference}.fai")
    output = pathlib.Path(args.output).resolve()
    base_temp_dir = pathlib.Path(args.temp_dir).resolve()
    if not input_vcf.is_file():
        raise HybridNormError(f"input VCF {input_vcf} does not exist")
    if not reference.is_file():
        raise HybridNormError(f"reference {reference} does not exist")
    if not output.parent.is_dir():
        raise HybridNormError(
            f"output directory {output.parent} does not exist"
        )
    if not base_temp_dir.is_dir():
        raise HybridNormError(
            f"temporary directory {base_temp_dir} does not exist"
        )

    temp_dir = pathlib.Path(
        tempfile.mkdtemp(prefix="hybrid-norm.", dir=base_temp_dir)
    )
    partial, partial_index = partial_paths(output)
    view_error_path = temp_dir / "view.stderr"
    bgzip_error_path = temp_dir / "bgzip.stderr"
    view_process: subprocess.Popen[bytes] | None = None
    bgzip_process: subprocess.Popen[bytes] | None = None
    success = False
    try:
        view_command = ["bcftools", "view", "-a"]
        if args.exclude_homref:
            view_command.extend(["-e", 'GT="0/0"'])
        view_command.append(str(input_vcf))
        with view_error_path.open("wb") as view_error:
            view_process = subprocess.Popen(
                view_command,
                stdout=subprocess.PIPE,
                stderr=view_error,
            )
            if view_process.stdout is None:
                view_process.terminate()
                raise HybridNormError(
                    "bcftools view stdout pipe was not created"
                )
            view_stdout = cast(BinaryIO, view_process.stdout)
            view_header, records = read_header_and_records(view_stdout)
            final_header = normalized_header(view_header, reference)
            candidate_header = add_marker_header(view_header)

            compression_threads = max(1, args.threads - 2)
            print(
                "hybrid_norm: "
                f"compression_threads={compression_threads} "
                f"batch_candidates={args.batch_candidates} "
                f"batch_bytes={args.batch_bytes} tmpdir={temp_dir}",
                file=sys.stderr,
            )
            with (
                partial.open("wb") as compressed_output,
                bgzip_error_path.open("wb") as bgzip_error,
            ):
                bgzip_process = subprocess.Popen(
                    ["bgzip", "-@", str(compression_threads), "-c"],
                    stdin=subprocess.PIPE,
                    stdout=compressed_output,
                    stderr=bgzip_error,
                )
                if bgzip_process.stdin is None:
                    bgzip_process.terminate()
                    raise HybridNormError("bgzip stdin pipe was not created")
                bgzip_stdin = cast(BinaryIO, bgzip_process.stdin)
                try:
                    bgzip_stdin.write(final_header)
                    with ReferenceReader(reference, reference_fai) as reader:
                        (
                            input_records,
                            candidates,
                            output_records,
                            batches,
                        ) = process_records(
                            records,
                            bgzip_stdin,
                            reference,
                            reader,
                            candidate_header,
                            temp_dir,
                            args.batch_candidates,
                            args.batch_bytes,
                        )
                except BaseException:
                    bgzip_stdin.close()
                    bgzip_process.terminate()
                    bgzip_process.wait()
                    raise
                bgzip_stdin.close()
                bgzip_return_code = bgzip_process.wait()

            view_stdout.close()
            view_return_code = view_process.wait()
        if view_return_code != 0:
            message = view_error_path.read_text(errors="replace").strip()
            raise HybridNormError(
                f"bcftools view failed with exit code {view_return_code}: "
                f"{message}"
            )
        if bgzip_return_code != 0:
            message = bgzip_error_path.read_text(errors="replace").strip()
            raise HybridNormError(
                f"BGZF publication failed with exit code {bgzip_return_code}: "
                f"{message}"
            )

        run_checked(
            ["tabix", "-f", "-p", "vcf", str(partial)],
            "tabix indexing",
        )
        run_checked(["tabix", "-l", str(partial)], "tabix validation")
        publish_pair(partial, partial_index, output)
        print(
            "hybrid_norm: "
            f"input_records={input_records} candidates={candidates} "
            f"output_records={output_records} batches={batches}",
            file=sys.stderr,
        )
        success = True
    except FileNotFoundError as error:
        raise HybridNormError(
            f"required executable {error.filename} is missing"
        ) from error
    finally:
        if view_process is not None and view_process.poll() is None:
            view_process.terminate()
            view_process.wait()
        if bgzip_process is not None and bgzip_process.poll() is None:
            bgzip_process.terminate()
            bgzip_process.wait()
        if partial.exists():
            partial.unlink()
        if partial_index.exists():
            partial_index.unlink()
        if success:
            shutil.rmtree(temp_dir)
        else:
            print(
                f"hybrid_norm: preserved failed work directory {temp_dir}",
                file=sys.stderr,
            )
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="sentieon pyexec hybrid_norm.py",
        usage=(
            "%(prog)s --input-vcf INPUT --reference REF --temp-dir DIR "
            "[options] output.vcf.gz"
        ),
    )
    parser.add_argument("output", help="output BGZF VCF")
    parser.add_argument("--input-vcf", required=True, help="model-applied VCF")
    parser.add_argument("--reference", required=True, help="reference FASTA")
    parser.add_argument(
        "--temp-dir", required=True, help="existing scratch directory"
    )
    parser.add_argument(
        "--exclude-homref",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "-t",
        "--threads",
        type=int,
        default=mp.cpu_count(),
        help="total thread budget",
    )
    parser.add_argument(
        "--batch-candidates",
        type=int,
        default=DEFAULT_BATCH_CANDIDATES,
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--batch-bytes",
        type=int,
        default=DEFAULT_BATCH_BYTES,
        help=argparse.SUPPRESS,
    )
    try:
        sys.exit(run_normalization(parser.parse_args()))
    except HybridNormError as error:
        print(f"Error: {error}", file=sys.stderr)
        sys.exit(1)
