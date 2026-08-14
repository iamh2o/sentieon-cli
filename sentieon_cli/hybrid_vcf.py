"""Post-model whole-contig finalization for the DNAscope Hybrid pipeline."""

from __future__ import annotations

import copy
import pathlib
import sys
from typing import List, Optional

import packaging.version

from .dag import DAG
from .job import Job
from .pipeline import BasePipeline
from .shell_pipeline import Command, Pipeline
from .shard import parse_fai
from .util import check_version, path_arg

HYBRID_VCF_MIN_VERSIONS = {
    "sentieon driver": packaging.version.Version("202503.01"),
    "bcftools": packaging.version.Version("1.22"),
}


def parse_contig_csv(value: str) -> List[str]:
    """Parse an ordered, duplicate-free comma-separated contig list."""

    contigs = [item.strip() for item in value.split(",")]
    if not contigs or any(not item for item in contigs):
        raise ValueError("--contigs must be a non-empty comma-separated list")
    if len(contigs) != len(set(contigs)):
        raise ValueError("--contigs must not contain duplicates")
    return contigs


def validate_fai_order(
    reference_fai: pathlib.Path, requested_contigs: List[str]
) -> None:
    """Require requested contigs to be an exact FAI-order subset."""

    fai_contigs = list(parse_fai(reference_fai))
    unknown = [
        contig for contig in requested_contigs if contig not in fai_contigs
    ]
    if unknown:
        raise ValueError(
            "requested contigs are absent from the reference FAI: "
            + ",".join(unknown)
        )
    positions = [fai_contigs.index(contig) for contig in requested_contigs]
    if positions != sorted(positions):
        raise ValueError("requested contigs are not in reference FAI order")


class HybridFinalizeContigPipeline(BasePipeline):
    """Finalize one whole contig from a post-DNAModelApply VCF."""

    params = copy.deepcopy(BasePipeline.params)
    params["cores"] = {
        "flags": ["-t", "--cores"],
        "help": "Exact CPU budget for each sequential finalization stage.",
        "required": True,
        "type": int,
    }
    params.update(
        {
            "contig": {
                "help": "Exact reference contig to finalize.",
                "required": True,
            },
            "emit_mode": {
                "help": "Retain gVCF hom-ref records or emit VCF records.",
                "choices": ["gvcf", "vcf"],
                "required": True,
            },
        }
    )
    positionals = {
        "input_vcf": {
            "help": "Indexed post-DNAModelApply input VCF.",
            "type": path_arg(exists=True, is_file=True),
        },
        "output_vcf": {
            "help": "Finalized contig VCF; name must end in .vcf.gz.",
            "type": path_arg(),
        },
    }

    def __init__(self) -> None:
        super().__init__()
        self.contig: Optional[str] = None
        self.emit_mode: Optional[str] = None
        self.input_vcf: Optional[pathlib.Path] = None

    def validate(self) -> None:
        if self.cores != 4:
            self.logger.error(
                "dnascope-hybrid-finalize-contig requires exactly 4 cores"
            )
            sys.exit(2)
        self.validate_ref()
        self.validate_output_vcf()
        assert self.reference is not None
        assert self.input_vcf is not None
        assert self.contig is not None
        fai = pathlib.Path(str(self.reference) + ".fai")
        if self.contig not in parse_fai(fai):
            self.logger.error(
                "--contig %s is absent from reference FAI %s", self.contig, fai
            )
            sys.exit(2)
        if not pathlib.Path(str(self.input_vcf) + ".tbi").is_file():
            self.logger.error(
                "indexed region selection requires %s.tbi", self.input_vcf
            )
            sys.exit(2)
        if not self.skip_version_check:
            for command, minimum in HYBRID_VCF_MIN_VERSIONS.items():
                if not check_version(command, minimum):
                    sys.exit(2)

    def configure(self) -> None:
        self.numa_nodes = []

    def build_dag(self) -> DAG:
        assert self.reference is not None
        assert self.input_vcf is not None
        assert self.output_vcf is not None
        assert self.contig is not None
        assert self.emit_mode is not None

        worker_threads = max(0, self.cores - 1)
        selected_vcf = self.tmp_dir / "selected.vcf.gz"
        repaired_vcf = self.tmp_dir / "reference-repaired.vcf.gz"
        normalized_vcf = self.tmp_dir / "normalized.vcf.gz"

        view_args = [
            "view",
            "--no-version",
            "--threads",
            str(worker_threads),
            "--regions",
            self.contig,
            "-a",
        ]
        if self.emit_mode == "vcf":
            view_args.extend(["-e", 'GT="0/0"'])
        view_args.extend(
            ["-O", "z", "-o", str(selected_vcf), str(self.input_vcf)]
        )
        select_job = Job(
            Pipeline(Command("bcftools", *view_args)),
            "select-contig",
            self.cores,
            task_name="hybrid-finalize",
        )
        repair_reference_job = Job(
            Pipeline(
                Command(
                    "bcftools",
                    "norm",
                    "--no-version",
                    "--threads",
                    str(worker_threads),
                    "--check-ref",
                    "s",
                    "-f",
                    str(self.reference),
                    "-O",
                    "z",
                    "-o",
                    str(repaired_vcf),
                    str(selected_vcf),
                )
            ),
            "repair-reference",
            self.cores,
            task_name="hybrid-finalize",
        )
        normalize_job = Job(
            Pipeline(
                Command(
                    "bcftools",
                    "norm",
                    "--no-version",
                    "--threads",
                    str(worker_threads),
                    "--check-ref",
                    "e",
                    "-f",
                    str(self.reference),
                    "-O",
                    "z",
                    "-o",
                    str(normalized_vcf),
                    str(repaired_vcf),
                )
            ),
            "normalize-contig",
            self.cores,
            task_name="hybrid-finalize",
        )
        convert_job = Job(
            Pipeline(
                Command(
                    "sentieon",
                    "util",
                    "vcfconvert",
                    "-t",
                    str(self.cores),
                    str(normalized_vcf),
                    str(self.output_vcf),
                )
            ),
            "convert-contig",
            self.cores,
            task_name="hybrid-finalize",
        )

        dag = DAG()
        dag.add_job(select_job)
        dag.add_job(repair_reference_job, {select_job})
        dag.add_job(normalize_job, {repair_reference_job})
        dag.add_job(convert_job, {normalize_job})
        return dag


class HybridGatherPipeline(BasePipeline):
    """Gather whole-contig VCFs in explicit reference order and index them."""

    params = copy.deepcopy(BasePipeline.params)
    del params["reference"]
    params["cores"] = {
        "flags": ["-t", "--cores"],
        "help": "Exact CPU budget for gather and index.",
        "required": True,
        "type": int,
    }
    params.update(
        {
            "reference_fai": {
                "help": "Reference FAI used to validate contig order.",
                "required": True,
                "type": path_arg(exists=True, is_file=True),
            },
            "contigs": {
                "help": (
                    "Ordered comma-separated contigs corresponding to inputs."
                ),
                "required": True,
            },
            "input_vcf": {
                "help": (
                    "One finalized VCF per contig, supplied in contig order."
                ),
                "action": "append",
                "required": True,
                "type": path_arg(exists=True, is_file=True),
            },
        }
    )
    positionals = copy.deepcopy(BasePipeline.positionals)

    def __init__(self) -> None:
        super().__init__()
        self.reference_fai: Optional[pathlib.Path] = None
        self.contigs: Optional[str] = None
        self.input_vcf: List[pathlib.Path] = []
        self.ordered_contigs: List[str] = []

    def validate(self) -> None:
        if self.cores != 8:
            self.logger.error(
                "dnascope-hybrid-gather requires exactly 8 cores"
            )
            sys.exit(2)
        self.validate_output_vcf()
        assert self.reference_fai is not None
        assert self.contigs is not None
        try:
            self.ordered_contigs = parse_contig_csv(self.contigs)
            validate_fai_order(self.reference_fai, self.ordered_contigs)
        except ValueError as error:
            self.logger.error("%s", error)
            sys.exit(2)
        if len(self.input_vcf) != len(self.ordered_contigs):
            self.logger.error(
                "--input_vcf count %d does not match --contigs count %d",
                len(self.input_vcf),
                len(self.ordered_contigs),
            )
            sys.exit(2)
        invalid = [
            path
            for path in self.input_vcf
            if not str(path).endswith(".vcf.gz")
        ]
        if invalid:
            self.logger.error("input VCFs must end in .vcf.gz: %s", invalid)
            sys.exit(2)
        if not self.skip_version_check:
            if not check_version(
                "bcftools", HYBRID_VCF_MIN_VERSIONS["bcftools"]
            ):
                sys.exit(2)

    def configure(self) -> None:
        self.numa_nodes = []

    def build_dag(self) -> DAG:
        assert self.output_vcf is not None
        worker_threads = max(0, self.cores - 1)
        gather_job = Job(
            Pipeline(
                Command(
                    "bcftools",
                    "concat",
                    "--no-version",
                    "--threads",
                    str(worker_threads),
                    "-O",
                    "z",
                    "-o",
                    str(self.output_vcf),
                    *[str(path) for path in self.input_vcf],
                )
            ),
            "gather-contigs",
            self.cores,
            task_name="hybrid-gather",
        )
        index_job = Job(
            Pipeline(
                Command(
                    "bcftools",
                    "index",
                    "--threads",
                    str(worker_threads),
                    "--tbi",
                    "--force",
                    str(self.output_vcf),
                )
            ),
            "index-gathered-vcf",
            self.cores,
            task_name="hybrid-gather",
        )
        dag = DAG()
        dag.add_job(gather_job)
        dag.add_job(index_job, {gather_job})
        return dag
