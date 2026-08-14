"""Bounded executor fixtures for the Hybrid Stage-1 split-worker topology."""

import pathlib
import sys

from sentieon_cli.dag import DAG
from sentieon_cli.executor import LocalExecutor
from sentieon_cli.job import Job
from sentieon_cli.scheduler import ThreadScheduler
from sentieon_cli.shell_pipeline import Command, InputProcSub, Pipeline


def _stage1_dag(tmp_path: pathlib.Path) -> tuple[DAG, dict[str, pathlib.Path]]:
    """Build a vendor-free analogue of the Stage-1 FIFO/sort topology."""
    fifo = tmp_path / "stage1_hap.fq"
    hap_bam = tmp_path / "stage1_hap.bam"
    aligned_bam = tmp_path / "hybrid_stage1.bam"
    stage2 = tmp_path / "stage2.txt"

    mkfifo = Job(
        Pipeline(Command("mkfifo", str(fifo))),
        "stage1-fifo",
        task_name="hybrid-realignment",
    )

    # The real HybridStage1 command writes FASTQ through the named FIFO while
    # its unsorted haplotype BAM travels on stdout into sentieon util sort.
    writer_code = (
        "import pathlib,sys; "
        "p=pathlib.Path(sys.argv[1]); "
        "f=p.open('w'); f.write('hap-a\\nhap-b\\n'); f.close(); "
        "sys.stdout.write('bam-a\\nbam-b\\n')"
    )
    writer = Job(
        Pipeline(
            Command(sys.executable, "-c", writer_code, str(fifo)),
            Command("cat"),
            file_output=hap_bam,
        ),
        "first-stage-hap",
        0,
        task_name="hybrid-realignment",
    )

    # The real companion job concatenates the FIFO before an insertion-model
    # process substitution, then sends the stream through BWA and util sort.
    validate_code = (
        "import sys; "
        "lines=sys.stdin.read().splitlines(); "
        "assert lines == ['hap-a','hap-b','ins-a'], lines; "
        "sys.stdout.write('aligned-ok\\n')"
    )
    reader = Job(
        Pipeline(
            Command(
                "cat",
                str(fifo),
                InputProcSub(
                    Pipeline(Command(sys.executable, "-c", "print('ins-a')"))
                ),
            ),
            Command(sys.executable, "-c", validate_code),
            file_output=aligned_bam,
        ),
        "first-stage",
        2,
        task_name="hybrid-realignment",
    )

    stage2_code = (
        "import pathlib,sys; "
        "assert pathlib.Path(sys.argv[1]).read_text() == 'bam-a\\nbam-b\\n'; "
        "assert pathlib.Path(sys.argv[2]).read_text() == 'aligned-ok\\n'; "
        "sys.stdout.write('stage2-ok\\n')"
    )
    stage2_job = Job(
        Pipeline(
            Command(
                sys.executable,
                "-c",
                stage2_code,
                str(hap_bam),
                str(aligned_bam),
            ),
            file_output=stage2,
        ),
        "second-stage",
        2,
        task_name="hybrid-realignment",
    )

    dag = DAG()
    dag.add_job(mkfifo)
    dag.add_job(writer, {mkfifo})
    dag.add_job(reader, {mkfifo})
    dag.add_job(stage2_job, {writer, reader})
    return dag, {
        "fifo": fifo,
        "hap_bam": hap_bam,
        "aligned_bam": aligned_bam,
        "stage2": stage2,
    }


def test_hybrid_stage1_split_workers_stress(tmp_path):
    """Repeated FIFO/proc-sub runs complete without deadlock or truncation."""
    for iteration in range(20):
        run_dir = tmp_path / f"run-{iteration}"
        run_dir.mkdir()
        dag, paths = _stage1_dag(run_dir)
        executor = LocalExecutor(
            ThreadScheduler(dag, 2),
            shutdown_grace_period=0.25,
            thread_pool_size=16,
        )
        executor.execute()

        assert executor.jobs_with_errors == []
        assert paths["stage2"].read_text() == "stage2-ok\n"
        assert not dag.ready_jobs
        assert not dag.waiting_jobs
