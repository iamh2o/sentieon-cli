import os
import pathlib
import shutil
import subprocess
import sys

import pytest

from sentieon_cli.command_strings import cmd_pyexec_hybrid_select
from sentieon_cli.scripts.hybrid_select import cut_shards

REPOSITORY_ROOT = pathlib.Path(__file__).parents[2]
HYBRID_SELECT = (
    REPOSITORY_ROOT / "sentieon_cli" / "scripts" / "hybrid_select.py"
)

INPUT_VCF = """\
##fileformat=VCFv4.2
##contig=<ID=chr1,length=50>
##contig=<ID=chr2,length=25>
##INFO=<ID=END,Number=1,Type=Integer,Description="End position">
##INFO=<ID=STR,Number=0,Type=Flag,Description="Short tandem repeat">
##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">
##FORMAT=<ID=LAD,Number=R,Type=Integer,Description="Long-read allelic depth">
##FORMAT=<ID=LPL,Number=G,Type=Integer,Description="Long-read likelihood">
##FORMAT=<ID=SPL,Number=G,Type=Integer,Description="Short-read likelihood">
#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\tSAMPLE
chr1\t1\t.\tA\t<NON_REF>\t.\t.\tEND=5\tGT:LAD:LPL:SPL\t0/0:1,1,0:0,40,50:0,5,10
chr1\t6\t.\tC\tT\t50\tPASS\t.\tGT:LAD:LPL:SPL\t0/1:1,0,0:0,40,50:0,5,10
chr1\t10\t.\tA\tG\t50\tPASS\t.\tGT:LAD:LPL:SPL\t0/1:2,2,0:0,10,20:0,5,10
chr1\t15\t.\tA\tG\t50\tPASS\t.\tGT:LAD:LPL:SPL\t0/1:2,2,0:0,40,50:0,40,50
chr1\t20\t.\tA\tG\t50\tPASS\tSTR\tGT:LAD:LPL:SPL\t0/1:2,2,0:0,40,50:40,0,50
chr1\t25\t.\tAA\tA\t50\tPASS\t.\tGT:LAD:LPL:SPL\t0/1:2,2,0:40,0,50:0,5,10
chr2\t1\t.\tG\tC\t50\tPASS\t.\tGT:LAD:LPL:SPL\t0/1:2,2,0:40,0,50:0,5,10
"""

EXPECTED_BED = """\
chr1\t0\t8
chr1\t21\t29
chr2\t0\t4
"""


def require_htslib_tools() -> tuple[str, str]:
    bgzip = shutil.which("bgzip")
    tabix = shutil.which("tabix")
    assert bgzip is not None, "bgzip is required for hybrid_select tests"
    assert tabix is not None, "tabix is required for hybrid_select tests"
    return bgzip, tabix


def make_indexed_vcf(tmp_path: pathlib.Path) -> pathlib.Path:
    bgzip, tabix = require_htslib_tools()
    source = tmp_path / "input.vcf"
    source.write_text(INPUT_VCF)
    compressed = tmp_path / "input.vcf.gz"
    with compressed.open("wb") as output:
        subprocess.run([bgzip, "-c", str(source)], check=True, stdout=output)
    subprocess.run([tabix, "-p", "vcf", str(compressed)], check=True)
    return compressed


def run_selector(
    tmp_path: pathlib.Path,
    input_vcf: pathlib.Path,
    threads: int,
    step_size: int,
) -> tuple[pathlib.Path, subprocess.CompletedProcess[str]]:
    reference_index = tmp_path / "reference.fa.fai"
    reference_index.write_text("chr1\t50\t0\t50\t51\nchr2\t25\t51\t25\t26\n")
    output = tmp_path / f"selected.{threads}.bed"
    scratch = tmp_path / f"scratch.{threads}"
    scratch.mkdir()
    environment = os.environ.copy()
    environment["SENTIEON_TMPDIR"] = str(scratch)
    result = subprocess.run(
        [
            sys.executable,
            str(HYBRID_SELECT),
            "-v",
            str(input_vcf),
            "--reference-fai",
            str(reference_index),
            "--slop-size",
            "3",
            "--step-size",
            str(step_size),
            "-t",
            str(threads),
            str(output),
        ],
        capture_output=True,
        text=True,
        env=environment,
    )
    return output, result


@pytest.mark.parametrize("threads", (1, 4))
def test_direct_bed_matches_v170_pipeline_semantics(
    tmp_path: pathlib.Path, threads: int
) -> None:
    input_vcf = make_indexed_vcf(tmp_path)
    output, result = run_selector(tmp_path, input_vcf, threads, 13)
    assert result.returncode == 0, result.stderr
    assert output.read_text() == EXPECTED_BED
    assert "records=7 selected=3" in result.stderr


def test_cross_contig_shard_carry_matches_vcflib() -> None:
    assert cut_shards([("chr1", 15), ("chr2", 10)], 10) == [
        (0, "chr1", 0, 10),
        (1, "chr1", 10, 15),
        (2, "chr2", 0, 5),
        (3, "chr2", 5, 10),
    ]


def test_missing_index_fails_atomically(tmp_path: pathlib.Path) -> None:
    input_vcf = make_indexed_vcf(tmp_path)
    pathlib.Path(f"{input_vcf}.tbi").unlink()
    output, result = run_selector(tmp_path, input_vcf, 1, 10)
    assert result.returncode == 1
    assert "input VCF index is missing" in result.stderr
    assert not output.exists()


def test_invalid_thread_count_fails_atomically(tmp_path: pathlib.Path) -> None:
    input_vcf = make_indexed_vcf(tmp_path)
    output, result = run_selector(tmp_path, input_vcf, 0, 10)
    assert result.returncode == 1
    assert "--threads must be at least 1" in result.stderr
    assert not output.exists()


def test_command_builder_is_one_direct_process(tmp_path: pathlib.Path) -> None:
    output = tmp_path / "selected.bed"
    input_vcf = tmp_path / "input.vcf.gz"
    reference_index = tmp_path / "reference.fa.fai"
    script = tmp_path / "hybrid_select.py"
    pipeline = cmd_pyexec_hybrid_select(
        output,
        input_vcf,
        reference_index,
        script,
        128,
    )
    assert len(pipeline.nodes) == 1
    command = pipeline.nodes[0]
    assert command.executable == sys.executable
    assert command.args == [
        str(script),
        "-v",
        str(input_vcf),
        "-t",
        "128",
        "--reference-fai",
        str(reference_index),
        "--slop-size",
        "1000",
        str(output),
    ]
