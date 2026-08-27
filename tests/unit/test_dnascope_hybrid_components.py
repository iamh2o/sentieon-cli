"""Component and ploidy contracts for the forked Hybrid pipeline."""

import argparse
import json
import pathlib
from unittest.mock import patch

import pytest

from sentieon_cli.dnascope_hybrid import (
    DNAscopeHybridPipeline,
    HYBRID_CORE_MODEL_MEMBERS,
)
from tests.utils.test_helpers import (
    setup_basic_test_environment,
    teardown_test_environment,
)


def _bundle_info() -> bytes:
    return json.dumps(
        {
            "bundleVersion": "1.2",
            "longReadPlatform": "ONT",
            "shortReadPlatform": "Illumina",
            "minScriptVersion": "1.0.0",
            "pipeline": "DNAscope Hybrid",
        }
    ).encode()


def _job_map(dag):
    jobs = list(dag.ready_jobs) + list(dag.waiting_jobs)
    return {job.name: job for job in jobs}


class TestHybridComponentModes:
    def setup_method(self):
        self.helper = setup_basic_test_environment()

    def teardown_method(self):
        teardown_test_environment(self.helper)

    def _pipeline(self) -> DNAscopeHybridPipeline:
        pipeline = self.helper.create_hybrid_pipeline()
        pipeline.bed = self.helper.fs.create_bed_file(
            "diploid.bed", [("chr1", 0, 100), ("chrX", 0, 10)]
        )
        pipeline.haploid_bed = self.helper.fs.create_bed_file(
            "haploid.bed", [("chrX", 10, 100), ("chrY", 0, 100)]
        )
        pipeline.skip_metrics = True
        pipeline.skip_mosdepth = True
        pipeline.skip_multiqc = True
        return pipeline

    @patch("sentieon_cli.command_strings.get_rg_lines")
    @patch("sentieon_cli.dnascope_hybrid.ar_load")
    def test_only_cnv_builds_two_ploidy_passes_and_sorted_combine(
        self, mock_ar_load, mock_get_rg
    ):
        pipeline = self._pipeline()
        pipeline.only_cnv = True
        mock_ar_load.side_effect = [_bundle_info(), ["cnv.model"]]
        mock_get_rg.return_value = ["@RG\tID:test\tSM:sample"]

        pipeline.validate()
        pipeline.configure()
        jobs = _job_map(pipeline.build_dag())

        assert {
            "CNVscope-diploid",
            "CNVModelApply-diploid",
            "CNVscope-haploid",
            "CNVModelApply-haploid",
            "combine-ploidy-cnv",
        }.issubset(jobs)
        assert "calling-1" not in jobs
        assert "LongReadSV" not in jobs

        diploid_cmd = jobs["CNVscope-diploid"].shell.nodes[0].args
        haploid_cmd = jobs["CNVscope-haploid"].shell.nodes[0].args
        assert str(pipeline.bed) in diploid_cmd
        assert str(pipeline.haploid_bed) in haploid_cmd

        combine = jobs["combine-ploidy-cnv"].shell.nodes
        assert combine[0].executable == "bcftools"
        assert combine[0].args[:2] == ["concat", "--threads"]
        assert "-aD" in combine[0].args
        assert combine[1].executable == "bcftools"
        assert combine[1].args[:1] == ["sort"]
        assert combine[2].executable == "sentieon"
        assert combine[2].args[:2] == ["util", "vcfconvert"]

    @patch("sentieon_cli.command_strings.get_rg_lines")
    @patch("sentieon_cli.dnascope_hybrid.ar_load")
    def test_only_svs_uses_reference_sorted_region_union(
        self, mock_ar_load, mock_get_rg
    ):
        pipeline = self._pipeline()
        pipeline.only_svs = True
        mock_ar_load.side_effect = [_bundle_info(), ["longreadsv.model"]]
        mock_get_rg.return_value = ["@RG\tID:test\tSM:sample"]

        pipeline.validate()
        pipeline.configure()
        dag = pipeline.build_dag()
        jobs = _job_map(dag)

        assert "hybrid-sv-region-union" in jobs
        assert "LongReadSV" in jobs
        assert "CNVscope-diploid" not in jobs
        assert "calling-1" not in jobs
        union = jobs["hybrid-sv-region-union"].shell.nodes
        assert union[0].executable == "cat"
        assert union[0].args == [
            str(pipeline.bed),
            str(pipeline.haploid_bed),
        ]
        assert union[1].executable == "bedtools"
        assert union[1].args[:3] == [
            "sort",
            "-faidx",
            str(pipeline.reference) + ".fai",
        ]
        assert (
            jobs["hybrid-sv-region-union"]
            in dag.waiting_jobs[jobs["LongReadSV"]]
        )
        sv_args = jobs["LongReadSV"].shell.nodes[0].args
        assert str(pipeline.tmp_dir / "hybrid_sv_regions.bed") in sv_args


class TestHybridComponentValidation:
    def _pipeline(self) -> DNAscopeHybridPipeline:
        pipeline = DNAscopeHybridPipeline()
        pipeline.setup_logging(argparse.Namespace(loglevel="WARNING"))
        pipeline.model_bundle = pathlib.Path("hybrid.bundle")
        return pipeline

    @patch("sentieon_cli.dnascope_hybrid.ar_load")
    def test_core_requires_every_hybrid_model_member(self, mock_ar_load):
        pipeline = self._pipeline()
        pipeline.skip_cnv = True
        pipeline.skip_svs = True
        mock_ar_load.side_effect = [_bundle_info(), ["hybrid.model"]]

        with pytest.raises(SystemExit) as exc:
            pipeline.validate_bundle()

        assert exc.value.code == 2

    @patch("sentieon_cli.dnascope_hybrid.ar_load")
    def test_core_only_accepts_exact_core_member_set(self, mock_ar_load):
        pipeline = self._pipeline()
        pipeline.skip_cnv = True
        pipeline.skip_svs = True
        mock_ar_load.side_effect = [
            _bundle_info(),
            sorted(HYBRID_CORE_MODEL_MEMBERS),
        ]

        pipeline.validate_bundle()

    def test_haploid_bed_without_diploid_bed_is_rejected(self):
        pipeline = self._pipeline()
        pipeline.only_cnv = True
        pipeline.haploid_bed = pathlib.Path("haploid.bed")

        with pytest.raises(SystemExit) as exc:
            pipeline.validate()

        assert exc.value.code == 2

    def test_haploid_core_is_blocked_until_vendor_contract_is_confirmed(self):
        pipeline = self._pipeline()
        pipeline.bed = pathlib.Path("diploid.bed")
        pipeline.haploid_bed = pathlib.Path("haploid.bed")

        with pytest.raises(SystemExit) as exc:
            pipeline.validate()

        assert exc.value.code == 2

    def test_haploid_bed_is_rejected_even_when_core_is_manually_skipped(self):
        pipeline = self._pipeline()
        pipeline.bed = pathlib.Path("diploid.bed")
        pipeline.haploid_bed = pathlib.Path("haploid.bed")
        pipeline.skip_small_variants = True

        with pytest.raises(SystemExit) as exc:
            pipeline.validate()

        assert exc.value.code == 2

    def test_overlapping_ploidy_beds_are_rejected(self, tmp_path):
        pipeline = self._pipeline()
        pipeline.only_cnv = True
        pipeline.bed = tmp_path / "diploid.bed"
        pipeline.haploid_bed = tmp_path / "haploid.bed"
        pipeline.bed.write_text("chrX\t0\t100\n")
        pipeline.haploid_bed.write_text("chrX\t90\t200\n")

        with pytest.raises(SystemExit) as exc:
            pipeline.validate()

        assert exc.value.code == 2

    def test_only_modes_are_mutually_exclusive(self):
        pipeline = self._pipeline()
        pipeline.only_cnv = True
        pipeline.only_svs = True

        with pytest.raises(SystemExit) as exc:
            pipeline.validate()

        assert exc.value.code == 2
