import gzip
import pathlib
import shutil
import subprocess
import sys

import pytest

from sentieon_cli.command_strings import cmd_pyexec_hybrid_norm
from sentieon_cli.scripts.hybrid_norm import (
    ReferenceReader,
    needs_normalization,
    strip_marker,
)

REPOSITORY_ROOT = pathlib.Path(__file__).parents[2]
HYBRID_NORM = REPOSITORY_ROOT / "sentieon_cli" / "scripts" / "hybrid_norm.py"

CHR1 = "ACGT" * 20
CHRUN = "C" * 24

INPUT_VCF = """\
##fileformat=VCFv4.2
##FILTER=<ID=PASS,Description="All filters passed">
##contig=<ID=chr1,length=80>
##contig=<ID=chrUn,length=24>
##INFO=<ID=END,Number=1,Type=Integer,Description="End position">
##INFO=<ID=AC,Number=A,Type=Integer,Description="Allele count">
##INFO=<ID=AN,Number=1,Type=Integer,Description="Allele number">
##INFO=<ID=IA,Number=A,Type=Integer,Description="Number A fixture">
##INFO=<ID=IR,Number=R,Type=Integer,Description="Number R fixture">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=FA,Number=A,Type=Integer,Description="Number A fixture">
##FORMAT=<ID=FR,Number=R,Type=Integer,Description="Number R fixture">
##FORMAT=<ID=FG,Number=G,Type=Integer,Description="Number G fixture">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE
chr1\t1\t.\tA\t<NON_REF>\t.\tPASS\tEND=3;AC=0;AN=2;IA=0;IR=2,0\tGT:FA:FR:FG\t0/0:0:2,0:0,10,20
chr1\t4\t.\tT\tC,<NON_REF>\t50\tPASS\tAC=1,0;AN=2;IA=4,0;IR=1,1,0\tGT:FA:FR:FG\t0/1:4,0:1,1,0:0,10,20,30,40,50
chr1\t5\t.\tA\t<NON_REF>\t.\tPASS\tEND=7;AC=0;AN=2;IA=0;IR=2,0\tGT:FA:FR:FG\t0/0:0:2,0:0,10,20
chr1\t8\t.\tTA\tCA,<NON_REF>\t45\tPASS\tAC=1,0;AN=2;IA=8,0;IR=1,1,0\tGT:FA:FR:FG\t0/1:8,0:1,1,0:0,10,20,30,40,50
chr1\t11\t.\tGT\tG,<NON_REF>\t44\tPASS\tAC=1,0;AN=2;IA=11,0;IR=1,1,0\tGT:FA:FR:FG\t0/1:11,0:1,1,0:0,10,20,30,40,50
chr1\t16\t.\tT\t<DEL>,<NON_REF>\t40\tPASS\tEND=18;AC=1,0;AN=2;IA=16,0;IR=1,1,0\tGT:FA:FR:FG\t0/1:16,0:1,1,0:0,10,20,30,40,50
chr1\t20\ta\tT\tA\t35\tPASS\tAC=1;AN=2;IA=20;IR=1,1\tGT:FA:FR:FG\t0/1:20:1,1:0,10,20
chr1\t20\tb\tT\tG\t34\tPASS\tAC=1;AN=1;IA=21;IR=0,1\tGT:FA:FR:FG\t1:21:0,1:0,10
chr1\t24\t.\tT\tC\t33\tPASS\tAC=0;AN=2;IA=24;IR=2,0\tGT:FA:FR:FG\t0/0:24:2,0:0,10,20
chr1\t28\t.\tT\tC\t32\tPASS\tAC=0;AN=0;IA=28;IR=0,0\tGT:FA:FR:FG\t./.:28:0,0:0,10,20
chrUn\t1\t.\tC\tA\t30\tPASS\tAC=1;AN=2;IA=31;IR=1,1\tGT:FA:FR:FG\t0/1:31:1,1:0,10,20
"""


def require_tools() -> tuple[str, str, str]:
    bcftools = shutil.which("bcftools")
    bgzip = shutil.which("bgzip")
    tabix = shutil.which("tabix")
    assert bcftools is not None, "bcftools is required"
    assert bgzip is not None, "bgzip is required"
    assert tabix is not None, "tabix is required"
    return bcftools, bgzip, tabix


def make_reference(tmp_path: pathlib.Path) -> pathlib.Path:
    reference = tmp_path / "reference.fa"
    contents = f">chr1\n{CHR1}\n>chrUn\n{CHRUN}\n"
    reference.write_text(contents)
    chr1_offset = len(">chr1\n")
    chrun_offset = chr1_offset + len(CHR1) + len("\n>chrUn\n")
    pathlib.Path(f"{reference}.fai").write_text(
        f"chr1\t{len(CHR1)}\t{chr1_offset}\t{len(CHR1)}\t{len(CHR1) + 1}\n"
        f"chrUn\t{len(CHRUN)}\t{chrun_offset}\t{len(CHRUN)}\t{len(CHRUN) + 1}\n"
    )
    return reference


def make_indexed_vcf(
    tmp_path: pathlib.Path, contents: str = INPUT_VCF
) -> pathlib.Path:
    _, bgzip, tabix = require_tools()
    source = tmp_path / "input.vcf"
    source.write_text(contents)
    compressed = tmp_path / "input.vcf.gz"
    with compressed.open("wb") as output:
        subprocess.run([bgzip, "-c", str(source)], check=True, stdout=output)
    subprocess.run([tabix, "-p", "vcf", str(compressed)], check=True)
    return compressed


def run_full_oracle(
    tmp_path: pathlib.Path,
    input_vcf: pathlib.Path,
    reference: pathlib.Path,
    exclude_homref: bool,
) -> pathlib.Path:
    bcftools, _, _ = require_tools()
    view_command = [bcftools, "view", "-a"]
    if exclude_homref:
        view_command.extend(["-e", 'GT="0/0"'])
    view_command.append(str(input_vcf))
    view = subprocess.run(view_command, capture_output=True)
    assert view.returncode == 0, view.stderr.decode(errors="replace")
    norm = subprocess.run(
        [bcftools, "norm", "-f", str(reference)],
        input=view.stdout,
        capture_output=True,
    )
    assert norm.returncode == 0, norm.stderr.decode(errors="replace")
    output = tmp_path / (
        "oracle.hard.vcf.gz" if exclude_homref else "oracle.g.vcf.gz"
    )
    publish = subprocess.run(
        [
            bcftools,
            "view",
            "--no-version",
            "-O",
            "z",
            "-o",
            str(output),
            "-W=tbi",
            "-",
        ],
        input=norm.stdout,
        capture_output=True,
    )
    assert publish.returncode == 0, publish.stderr.decode(errors="replace")
    return output


def run_selective(
    tmp_path: pathlib.Path,
    input_vcf: pathlib.Path,
    reference: pathlib.Path,
    exclude_homref: bool,
) -> tuple[pathlib.Path, subprocess.CompletedProcess[str]]:
    output = tmp_path / (
        "selective.hard.vcf.gz" if exclude_homref else "selective.g.vcf.gz"
    )
    scratch = tmp_path / ("scratch-hard" if exclude_homref else "scratch-gvcf")
    scratch.mkdir()
    command = [
        sys.executable,
        str(HYBRID_NORM),
        "--input-vcf",
        str(input_vcf),
        "--reference",
        str(reference),
        "--temp-dir",
        str(scratch),
        "--threads",
        "4",
        "--batch-candidates",
        "2",
        "--batch-bytes",
        "250",
    ]
    if exclude_homref:
        command.append("--exclude-homref")
    command.append(str(output))
    result = subprocess.run(command, capture_output=True, text=True)
    return output, result


def decompressed(path: pathlib.Path) -> str:
    with gzip.open(path, "rt") as input_vcf:
        return input_vcf.read()


def record_body(path: pathlib.Path) -> list[str]:
    return [
        line
        for line in decompressed(path).splitlines()
        if not line.startswith("#")
    ]


def semantic_header(path: pathlib.Path) -> list[str]:
    return [
        line
        for line in decompressed(path).splitlines()
        if line.startswith("#") and not line.startswith("##bcftools_")
    ]


@pytest.mark.parametrize("exclude_homref", (False, True))
def test_selective_normalization_matches_full_pipeline(
    tmp_path: pathlib.Path, exclude_homref: bool
) -> None:
    reference = make_reference(tmp_path)
    input_vcf = make_indexed_vcf(tmp_path)
    oracle = run_full_oracle(tmp_path, input_vcf, reference, exclude_homref)
    selective, result = run_selective(
        tmp_path, input_vcf, reference, exclude_homref
    )
    assert result.returncode == 0, result.stderr
    assert pathlib.Path(f"{selective}.tbi").is_file()
    assert record_body(selective) == record_body(oracle)
    assert semantic_header(selective) == semantic_header(oracle)
    assert "candidates=3" in result.stderr
    assert "batches=" in result.stderr

    _, _, tabix = require_tools()
    for region in ("chr1:1-28", "chr1:8-20", "chrUn:1-24"):
        expected = subprocess.check_output([tabix, str(oracle), region])
        observed = subprocess.check_output([tabix, str(selective), region])
        assert observed == expected


def test_reference_reader_supports_bgzf_without_external_gzi(
    tmp_path: pathlib.Path,
) -> None:
    _, bgzip, _ = require_tools()
    reference = make_reference(tmp_path)
    compressed = tmp_path / "reference.fa.bgz"
    with compressed.open("wb") as output:
        subprocess.run(
            [bgzip, "-c", str(reference)], check=True, stdout=output
        )
    compressed_fai = pathlib.Path(f"{compressed}.fai")
    compressed_fai.write_bytes(pathlib.Path(f"{reference}.fai").read_bytes())
    with ReferenceReader(compressed, compressed_fai) as reader:
        assert reader.base("chr1", 0) == b"A"
        assert reader.base("chr1", 79) == b"T"
        assert reader.base("chrUn", 0) == b"C"
        assert reader.base("chrUn", 23) == b"C"


def test_simple_snp_and_homref_are_passthrough_candidates() -> None:
    assert not needs_normalization(b"A", b".")
    assert not needs_normalization(b"A", b"C")
    assert not needs_normalization(b"A", b"C,G")
    assert not needs_normalization(b"A", b"<NON_REF>")
    assert not needs_normalization(b"A", b"C,<NON_REF>")
    assert needs_normalization(b"AT", b"CT")
    assert needs_normalization(b"AT", b"A,<NON_REF>")
    assert needs_normalization(b"A", b"<DEL>")
    assert needs_normalization(b"A", b"*")


def test_marker_restores_multiple_records_and_is_stripped() -> None:
    first = (
        b"chr1\t8\t.\tT\tC\t40\tPASS\t"
        b"DP=3;SENTIEON_HYBRID_NORM_ORDINAL=9\tGT\t0/1\n"
    )
    second = (
        b"chr1\t8\t.\tT\tG\t40\tPASS\t"
        b"SENTIEON_HYBRID_NORM_ORDINAL=9\tGT\t0/1\n"
    )
    assert strip_marker(first) == (
        9,
        b"chr1\t8\t.\tT\tC\t40\tPASS\tDP=3\tGT\t0/1\n",
    )
    assert strip_marker(second) == (
        9,
        b"chr1\t8\t.\tT\tG\t40\tPASS\t.\tGT\t0/1\n",
    )


def test_passthrough_reference_mismatch_fails_atomically(
    tmp_path: pathlib.Path,
) -> None:
    reference = make_reference(tmp_path)
    mismatched = INPUT_VCF.replace(
        "chr1\t20\ta\tT\tA",
        "chr1\t20\ta\tC\tA",
    )
    input_vcf = make_indexed_vcf(tmp_path, mismatched)
    output = tmp_path / "selective.g.vcf.gz"
    output.write_bytes(b"existing output")
    output_index = pathlib.Path(f"{output}.tbi")
    output_index.write_bytes(b"existing index")
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    result = subprocess.run(
        [
            sys.executable,
            str(HYBRID_NORM),
            "--input-vcf",
            str(input_vcf),
            "--reference",
            str(reference),
            "--temp-dir",
            str(scratch),
            "--threads",
            "2",
            str(output),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "reference mismatch at chr1:20" in result.stderr
    assert output.read_bytes() == b"existing output"
    assert output_index.read_bytes() == b"existing index"


def test_command_builder_uses_one_process(tmp_path: pathlib.Path) -> None:
    output = tmp_path / "output.vcf.gz"
    input_vcf = tmp_path / "input.vcf.gz"
    reference = tmp_path / "reference.fa"
    scratch = tmp_path / "scratch"
    script = tmp_path / "hybrid_norm.py"
    pipeline = cmd_pyexec_hybrid_norm(
        output,
        input_vcf,
        reference,
        scratch,
        script,
        128,
        True,
    )
    assert len(pipeline.nodes) == 1
    command = pipeline.nodes[0]
    assert command.executable == sys.executable
    assert command.args == [
        str(script),
        "--input-vcf",
        str(input_vcf),
        "--reference",
        str(reference),
        "--temp-dir",
        str(scratch),
        "--threads",
        "128",
        "--exclude-homref",
        str(output),
    ]
