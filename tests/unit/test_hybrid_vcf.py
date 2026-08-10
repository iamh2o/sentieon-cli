"""Tests for the Hybrid model checkpoint and whole-contig finalizer."""

from __future__ import annotations

import pathlib
import sys

import pytest

import sentieon_cli
from sentieon_cli import command_strings as cmds
from sentieon_cli.hybrid_vcf import (
    HybridFinalizeContigPipeline,
    HybridGatherPipeline,
    parse_contig_csv,
    validate_fai_order,
)
from tests.utils.test_helpers import (
    create_mock_args,
    setup_basic_test_environment,
)


def _write_fai(path: pathlib.Path) -> None:
    path.write_text(
        "chr1\t1000\t0\t80\t81\n"
        "chr19\t900\t1013\t80\t81\n"
        "chr20\t800\t1925\t80\t81\n",
        encoding="utf-8",
    )


def _all_jobs(dag):
    return [*dag.ready_jobs, *dag.waiting_jobs]


def _prepare_hybrid_dag_pipeline(pipeline) -> None:
    pipeline.lr_aln_readgroups = [[{"ID": "lr1", "SM": "sample"}]]
    pipeline.sr_aln_readgroups = [[{"ID": "sr1", "SM": "sample"}]]
    pipeline.hybrid_rg_sm = "sample"
    pipeline.hybrid_set_rg = False
    pipeline.shortread_tech = "Illumina"
    pipeline.longread_tech = "ONT"


def test_public_help_lists_hybrid_finalize_commands(
    monkeypatch, capsys
) -> None:
    monkeypatch.setattr(sys, "argv", ["sentieon-cli", "--help"])
    with pytest.raises(SystemExit) as error:
        sentieon_cli.main()
    assert error.value.code == 0
    help_text = capsys.readouterr().out
    assert "dnascope-hybrid-finalize-contig" in help_text
    assert "dnascope-hybrid-gather" in help_text


def test_stop_after_model_apply_omits_only_final_norm() -> None:
    helper = setup_basic_test_environment()
    try:
        pipeline = helper.create_hybrid_pipeline(cores=8)
        _prepare_hybrid_dag_pipeline(pipeline)
        pipeline.stop_after_model_apply = True
        dag = pipeline.build_dag()
        jobs = {job.name: job for job in _all_jobs(dag)}

        assert "model-apply" in jobs
        assert "final-norm" not in jobs
        assert "LongReadSV" in jobs
        assert "CNVModelApply" in jobs
        assert str(pipeline.output_vcf) in str(jobs["model-apply"].shell)
    finally:
        helper.cleanup()


def test_default_hybrid_dag_retains_final_norm() -> None:
    helper = setup_basic_test_environment()
    try:
        pipeline = helper.create_hybrid_pipeline(cores=8)
        _prepare_hybrid_dag_pipeline(pipeline)
        dag = pipeline.build_dag()
        jobs = {job.name: job for job in _all_jobs(dag)}
        assert "model-apply" in jobs
        assert "final-norm" in jobs
        assert jobs["final-norm"].threads == 6
        assert "--threads 1" in str(jobs["final-norm"].shell)
        assert "vcfconvert -t 2" in str(jobs["final-norm"].shell)
    finally:
        helper.cleanup()


def test_stop_and_skip_model_apply_are_mutually_exclusive() -> None:
    helper = setup_basic_test_environment()
    try:
        pipeline = helper.create_hybrid_pipeline()
        pipeline.stop_after_model_apply = True
        pipeline.skip_model_apply = True
        with pytest.raises(SystemExit) as error:
            pipeline.validate()
        assert error.value.code == 2
    finally:
        helper.cleanup()


def test_reachable_subset_and_concat_commands_use_thread_flags(
    tmp_path,
) -> None:
    subset = cmds.bcftools_subset(
        tmp_path / "subset.vcf.gz",
        tmp_path / "mix.vcf.gz",
        tmp_path / "regions.bed",
        bcftools_threads=1,
        vcfconvert_threads=2,
    )
    concat = cmds.bcftools_concat(
        tmp_path / "combined.vcf.gz",
        [tmp_path / "one.vcf.gz", tmp_path / "two.vcf.gz"],
        threads=3,
    )
    assert "bcftools view --threads 1" in str(subset)
    assert "sentieon util vcfconvert -t 2" in str(subset)
    assert "bcftools concat --threads 3" in str(concat)
    assert "bcftools sort --threads" not in str(subset) + str(concat)


def test_finalize_contig_builds_three_sequential_full_budget_jobs(
    tmp_path,
) -> None:
    reference = tmp_path / "reference.fa"
    reference.touch()
    _write_fai(tmp_path / "reference.fa.fai")
    input_vcf = tmp_path / "model.vcf.gz"
    input_vcf.touch()
    pathlib.Path(str(input_vcf) + ".tbi").touch()

    pipeline = HybridFinalizeContigPipeline()
    pipeline.setup_logging(create_mock_args())
    pipeline.reference = reference
    pipeline.contig = "chr19"
    pipeline.emit_mode = "gvcf"
    pipeline.input_vcf = input_vcf
    pipeline.output_vcf = tmp_path / "chr19.vcf.gz"
    pipeline.cores = 4
    pipeline.dry_run = True
    pipeline.skip_version_check = True
    pipeline.tmp_dir = tmp_path / "work"
    pipeline.tmp_dir.mkdir()
    pipeline.validate()
    pipeline.configure()
    dag = pipeline.build_dag()

    jobs = {job.name: job for job in _all_jobs(dag)}
    assert list(jobs) == [
        "select-contig",
        "normalize-contig",
        "convert-contig",
    ]
    assert all(job.threads == 4 for job in jobs.values())
    assert dag.waiting_jobs[jobs["normalize-contig"]] == {
        jobs["select-contig"]
    }
    assert dag.waiting_jobs[jobs["convert-contig"]] == {
        jobs["normalize-contig"]
    }
    assert "view --no-version --threads 3 --regions chr19 -a" in str(
        jobs["select-contig"].shell
    )
    assert "norm --no-version --threads 3" in str(
        jobs["normalize-contig"].shell
    )
    assert "vcfconvert -t 4" in str(jobs["convert-contig"].shell)


def test_finalize_vcf_mode_excludes_homref(tmp_path) -> None:
    pipeline = HybridFinalizeContigPipeline()
    pipeline.reference = tmp_path / "reference.fa"
    pipeline.input_vcf = tmp_path / "model.vcf.gz"
    pipeline.output_vcf = tmp_path / "chr19.vcf.gz"
    pipeline.contig = "chr19"
    pipeline.emit_mode = "vcf"
    pipeline.cores = 4
    pipeline.tmp_dir = tmp_path
    dag = pipeline.build_dag()
    select_job = next(
        job for job in _all_jobs(dag) if job.name == "select-contig"
    )
    assert "-e 'GT=\"0/0\"'" in str(select_job.shell)


def test_finalize_requires_exact_four_core_budget(tmp_path) -> None:
    pipeline = HybridFinalizeContigPipeline()
    pipeline.setup_logging(create_mock_args())
    pipeline.cores = 3
    with pytest.raises(SystemExit) as error:
        pipeline.validate()
    assert error.value.code == 2


def test_gather_requires_reference_order_and_matching_inputs(tmp_path) -> None:
    reference_fai = tmp_path / "reference.fa.fai"
    _write_fai(reference_fai)
    chr19 = tmp_path / "chr19.vcf.gz"
    chr20 = tmp_path / "chr20.vcf.gz"
    chr19.touch()
    chr20.touch()

    pipeline = HybridGatherPipeline()
    pipeline.setup_logging(create_mock_args())
    pipeline.reference_fai = reference_fai
    pipeline.contigs = "chr19,chr20"
    pipeline.input_vcf = [chr19, chr20]
    pipeline.output_vcf = tmp_path / "gathered.vcf.gz"
    pipeline.cores = 8
    pipeline.dry_run = True
    pipeline.skip_version_check = True
    pipeline.validate()
    pipeline.configure()
    dag = pipeline.build_dag()

    jobs = {job.name: job for job in _all_jobs(dag)}
    assert jobs["gather-contigs"].threads == 8
    assert jobs["index-gathered-vcf"].threads == 8
    gather_command = str(jobs["gather-contigs"].shell)
    assert "concat --no-version --threads 7" in gather_command
    assert gather_command.index(str(chr19)) < gather_command.index(str(chr20))
    assert dag.waiting_jobs[jobs["index-gathered-vcf"]] == {
        jobs["gather-contigs"]
    }


def test_gather_requires_exact_eight_core_budget(tmp_path) -> None:
    pipeline = HybridGatherPipeline()
    pipeline.setup_logging(create_mock_args())
    pipeline.cores = 7
    with pytest.raises(SystemExit) as error:
        pipeline.validate()
    assert error.value.code == 2


def test_contig_parser_and_fai_order_fail_hard(tmp_path) -> None:
    reference_fai = tmp_path / "reference.fa.fai"
    _write_fai(reference_fai)
    assert parse_contig_csv("chr19,chr20") == ["chr19", "chr20"]
    with pytest.raises(ValueError, match="duplicates"):
        parse_contig_csv("chr19,chr19")
    with pytest.raises(ValueError, match="FAI order"):
        validate_fai_order(reference_fai, ["chr20", "chr19"])
    with pytest.raises(ValueError, match="absent"):
        validate_fai_order(reference_fai, ["chr21"])
