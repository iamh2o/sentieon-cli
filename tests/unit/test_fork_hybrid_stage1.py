"""Contracts for the Sentieon 202503.04 Hybrid Stage-1 split workers."""

import packaging.version

from sentieon_cli.dnascope_hybrid import (
    CALLING_MIN_VERSIONS,
    DNAscopeHybridPipeline,
)
from tests.utils.test_helpers import (
    setup_basic_test_environment,
    teardown_test_environment,
)


def _jobs(dag):
    return {
        job.name: job
        for job in [*dag.ready_jobs.keys(), *dag.waiting_jobs.keys()]
    }


def _dependency_names(dag, job):
    return {dependency.name for dependency in dag.waiting_jobs.get(job, set())}


class TestDNAscopeHybridStage1:
    """Prove the upstream Stage-1 FIFO, sort, and DAG ordering contract."""

    def setup_method(self):
        self.helper = setup_basic_test_environment()
        self.pipeline: DNAscopeHybridPipeline = (
            self.helper.create_hybrid_pipeline(cores=2)
        )
        self.pipeline.lr_aln_readgroups = [
            [{"ID": "lr1", "SM": "sample"}]
        ]
        self.pipeline.sr_aln_readgroups = [
            [{"ID": "sr1", "SM": "sample"}]
        ]
        self.pipeline.hybrid_rg_sm = "sample"
        self.pipeline.hybrid_set_rg = False
        self.pipeline.shortread_tech = "Illumina"
        self.pipeline.longread_tech = "ONT"
        self.dag = self.pipeline.build_dag()
        self.jobs = _jobs(self.dag)

    def teardown_method(self):
        teardown_test_environment(self.helper)

    def test_driver_minimum_is_20250304(self):
        assert CALLING_MIN_VERSIONS["sentieon driver"] == (
            packaging.version.Version("202503.04")
        )

    def test_fifo_precedes_both_stage1_workers(self):
        fifo_job = self.jobs["stage1-fifo"]
        assert str(fifo_job.shell) == (
            f"mkfifo {self.pipeline.tmp_dir / 'stage1_hap.fq'}"
        )
        assert _dependency_names(self.dag, fifo_job) == set()
        expected = {"stage1-fifo", "concat-merge-bed"}
        assert _dependency_names(
            self.dag, self.jobs["first-stage-hap"]
        ) == expected
        assert _dependency_names(
            self.dag, self.jobs["first-stage"]
        ) == expected

    def test_haplotype_worker_sorts_unsorted_bam_stdout(self):
        hap_job = self.jobs["first-stage-hap"]
        command = str(hap_job.shell)
        assert "--algo HybridStage1" in command
        assert "HybridStage1.model" in command
        assert "--hap_bam -" in command
        assert "sentieon util sort" in command
        assert f"-o {self.pipeline.tmp_dir / 'stage1_hap.bam'}" in command
        assert "--sam2bam" not in command
        assert str(self.pipeline.tmp_dir / "stage1_hap.fq") in command
        assert hap_job.threads == 0

    def test_bwa_worker_reads_fifo_without_second_haplotype_driver(self):
        command = str(self.jobs["first-stage"].shell)
        assert command.startswith(
            f"cat {self.pipeline.tmp_dir / 'stage1_hap.fq'} "
        )
        assert "--hap_bam" not in command
        assert "HybridStage1.model" not in command
        assert "HybridStage1_ins.model" in command
        assert "sentieon bwa mem" in command
        assert "--sam2bam" in command

    def test_hybrid_stage2_waits_for_both_sorted_stage1_products(self):
        assert _dependency_names(
            self.dag, self.jobs["second-stage"]
        ) == {"first-stage", "first-stage-hap"}
        assert _dependency_names(self.dag, self.jobs["rm-tmp2"]) == {
            "first-stage",
            "first-stage-hap",
        }
        command = str(self.jobs["second-stage"].shell)
        assert f"--input {self.pipeline.tmp_dir / 'stage1_hap.bam'}" in command
        assert (
            f"--input {self.pipeline.tmp_dir / 'hybrid_stage1.bam'}" in command
        )

