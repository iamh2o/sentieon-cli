[![CI](https://github.com/Sentieon/sentieon-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/Sentieon/sentieon-cli/actions/workflows/ci.yml)

# Sentieon CLI

A command-line interface for the Sentieon software

## Install using pip (recommended)

Install the sentieon-cli into your python environment with `pip`:
```sh
pip install sentieon_cli
```

## Install with docker/podman

Install the sentieon-cli through a container image:
```sh
docker pull sentieon/sentieon_cli:latest
docker run --rm -v "$PWD:/data" -w /data \
    sentieon/sentieon_cli:latest \
    sentieon-cli dnascope-pangenome --help
```

## Installation with Poetry

Create a new python virtual environment for the project, if needed:
```
# Create a new venv, if needed
python3 -m venv /path/to/new/virtual/environment/sentieon_cli

# Activate the venv
source /path/to/new/virtual/environment/sentieon_cli/bin/activate
```

`sentieon-cli` uses [poetry](https://pypi.org/project/poetry/) for packaging and dependency management. Initially, you will need to install poetry:
```
pip install poetry
```

Clone this repository and cd into the root directory:
```
git clone https://github.com/sentieon/sentieon-cli.git
cd sentieon-cli
```

Use poetry to install the `sentieon-cli` into the virtual environment:
```
poetry install
```

You can then run commands from the virtual environment:
```
sentieon-cli ...
```

## Global arguments
The `sentieon-cli` supports the following global arguments:
- `--verbose` (`-v`): verbose logging. This is the default.
- `--quiet` (`-q`): only log warnings and errors.
- `--debug` (`-d`): debugging mode for more verbose logging. Takes precedence over `--verbose` and `--quiet`.

## Logging
Each run writes its log files to a directory next to the output VCF, named after the output file with the `.vcf.gz` suffix replaced by `_logs`, so `sample.vcf.gz` produces `sample_logs/`. The directory records the invocation in `command.txt`, the pipeline's own messages in `run.log`, and the output of each tool under `task_logs/`. Every pipeline accepts a `--log_dir` argument to write these files elsewhere. Rerunning a pipeline with the same output overwrites the logs of the previous run.

## Supported pipelines
- [**DNAscope**](https://support.sentieon.com/docs/sentieon_cli/#dnascope) - DNAscope pipeline implementation for germline SNV and indel calling from short read data.
- [**DNAscope LongRead**](https://support.sentieon.com/docs/sentieon_cli/#dnascope-longread) - DNAscope LongRead pipeline implementations for germline SNV and indel calling from long read data.
- [**DNAscope Hybrid**](https://support.sentieon.com/docs/sentieon_cli/#dnascope-hybrid) - DNAscope short-long-hybrid pipeline.
- [**DNAscope Pangenome**](https://support.sentieon.com/docs/sentieon_cli/#dnascope-pangenome) - DNAscope pangenome alignment and variant calling. Our recommended pipeline for short-read small variant calling.

## Hybrid model checkpoint and finalization

`dnascope-hybrid --stop-after-model-apply` keeps the ordinary Hybrid DAG
through `DNAModelApply`, including LongReadSV, CNVscope, and realigned-read
outputs, but writes the positional VCF before the historical final
normalization pipeline. The option is additive and off by default. It cannot
be combined with `--skip-model-apply`.

The checkpoint can be finalized as independently scheduled whole-contig jobs:

```sh
sentieon-cli dnascope-hybrid-finalize-contig \
    -r reference.fa -t 4 --contig chr19 --emit-mode gvcf \
    model-applied.g.vcf.gz chr19.final.g.vcf.gz
```

Each finalizer preserves the established `view -a`, `norm -f`, and Sentieon
`vcfconvert` order. It requires the checkpoint's `.tbi`, accepts only an exact
FAI contig, and uses its declared CPU budget sequentially rather than
oversubscribing a shell pipeline.

Gather finalized contigs by supplying the same number of ordered contigs and
VCFs:

```sh
sentieon-cli dnascope-hybrid-gather \
    --reference-fai reference.fa.fai --contigs chr19,chr20 -t 8 \
    --input-vcf chr19.final.g.vcf.gz \
    --input-vcf chr20.final.g.vcf.gz \
    gathered.g.vcf.gz
```

Gather rejects unknown, duplicate, or out-of-FAI-order contigs and creates the
final tabix index. There is no implicit contig discovery or filename-order
fallback.

## Hybrid component and ploidy modes

`dnascope-hybrid --only_cnv` runs only CNVscope. With both `-b` and
`--haploid_bed`, it runs separate diploid and haploid CNVscope/ModelApply
passes and combines their records in reference-header order.

`dnascope-hybrid --only_svs` runs only LongReadSV. With both BED arguments,
LongReadSV receives a reference-sorted merged union of the diploid and haploid
regions.

The requested component's model member is mandatory. Ordinary Hybrid mode
requires all Hybrid small-variant model members plus the CNV and SV members
unless those components are explicitly skipped; a missing member is never
silently converted into a skipped component.

`--haploid_bed` is accepted only with `--only_cnv` or `--only_svs`. Ordinary
Hybrid small-variant/gVCF mode keeps its documented diploid BED contract; the
CLI rejects haploid BED input instead of silently inventing unsupported Hybrid
small-variant semantics.

## License
Unless otherwise indicated, files in this repository are licensed under a BSD 2-Clause License.
