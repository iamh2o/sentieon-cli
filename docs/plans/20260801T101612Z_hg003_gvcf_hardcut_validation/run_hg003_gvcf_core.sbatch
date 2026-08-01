#!/usr/bin/env bash
# Run one directly timed HG003 gVCF Hybrid CLI lane.
# Submit only with:
#   sbatch --partition i128nvme --comment RnD --cpus-per-task=128 \
#     ./run_hg003_gvcf_core.sbatch \
#     <official170|release171i> <analysis-root> <exact-tag-checkout>

#SBATCH --cpus-per-task=128
#SBATCH --partition=i128nvme
#SBATCH --time=12:00:00
#SBATCH --comment=RnD

set -euo pipefail

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

[[ $# -eq 3 ]] \
    || die "usage: $0 <official170|release171i> <analysis-root> <exact-tag-checkout>"
candidate=$1
analysis_root=$2
source_checkout=$3

expected_root=/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x
[[ $analysis_root == "$expected_root" ]] \
    || die "unexpected analysis root: $analysis_root"
[[ $candidate == official170 || $candidate == release171i ]] \
    || die "invalid candidate: $candidate"
[[ ${SLURM_JOB_ID-} =~ ^[0-9]+$ ]] || die "run this payload through sbatch"
[[ ${SLURM_CPUS_PER_TASK-} == 128 ]] \
    || die "requires --cpus-per-task=128"
[[ ${SLURM_JOB_PARTITION-} == i128nvme ]] \
    || die "requires --partition=i128nvme"

case $candidate in
    official170)
        expected_sha=1bf377d3ce79fc4d8c2dc221e1f696441e38349d
        expected_tag=v1.7.0
        expected_source_version=1.7.0
        source_repository=https://github.com/Sentieon/sentieon-cli.git
        ;;
    release171i)
        expected_sha=e4f0ff8bf4ddd882cb154774178d2b40babba056
        expected_tag=1.7.1i
        expected_source_version=1.7.1+i
        source_repository=https://github.com/iamh2o/sentieon-cli.git
        ;;
esac

oracle_prefix=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/720569eabf1f3dc6300b2b50526585ed_
sentieon_root=/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.03
reference=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/fasta_fai_minalt/GRCh38_no_alt_analysis_set.fasta
model_bundle=$sentieon_root/bundles/HybridIlluminaONT2.0.bundle
dbsnp=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/gatk/Homo_sapiens_assembly38.dbsnp138.vcf.gz
population_vcf=/fsx/references/genomic_data/organism_references/H_sapiens/panhg38/pop-v20g41-20251216.vcf.gz
scope_bed=$analysis_root/inputs/full-primary.bed
expected_scope_sha=6f6179a3bc159e9527a56e665f8e5363fb8ee4af58696fbbdd043d1e0df6128d
analysis_unit=HG003-5X-CLI-RUNTIME
sr_cram=$analysis_root/prepared/$analysis_unit.sr.prepared.cram
lr_cram=$analysis_root/prepared/$analysis_unit.lr.aligned.cram
publish_dir=$analysis_root/results/$candidate/gvcf
checkout_runner=$analysis_root/validation-source/docs/plans/20260801T044918Z_sentieon_hybrid_core_runtime_171i_assets/run_checkout_cli.py

[[ ! -e $publish_dir ]] || die "publish destination already exists: $publish_dir"
[[ -d $source_checkout/.git || -f $source_checkout/.git ]] \
    || die "source path is not a Git checkout: $source_checkout"
source_sha=$(git -C "$source_checkout" rev-parse HEAD)
[[ $source_sha == "$expected_sha" ]] \
    || die "$candidate checkout is $source_sha, expected $expected_sha"
[[ -z $(git -C "$source_checkout" status --porcelain) ]] \
    || die "$candidate checkout is dirty"
tag_sha=$(git -C "$source_checkout" rev-parse "$expected_tag^{}")
[[ $tag_sha == "$expected_sha" ]] \
    || die "$expected_tag resolves to $tag_sha, expected $expected_sha"
if [[ $candidate == release171i ]]; then
    tag_type=$(git -C "$source_checkout" cat-file -t "$expected_tag")
    [[ $tag_type == tag ]] || die "$expected_tag is not an annotated tag"
fi

for required_path in \
    "$reference" "$reference.fai" "$model_bundle" "$dbsnp" "$dbsnp.tbi" \
    "$population_vcf" "$population_vcf.tbi" "$scope_bed" "$sr_cram" \
    "$sr_cram.crai" "$lr_cram" "$lr_cram.crai" \
    "$oracle_prefix/bin/python" "$oracle_prefix/bin/bcftools" \
    "$oracle_prefix/bin/bgzip" "$oracle_prefix/bin/tabix" \
    "$sentieon_root/bin/sentieon" "$checkout_runner"
do
    [[ -e $required_path ]] || die "required input/tool is missing: $required_path"
done
scope_sha=$(sha256sum "$scope_bed" | awk '{print $1}')
[[ $scope_sha == "$expected_scope_sha" ]] \
    || die "full-primary scope SHA-256 mismatch"

export SENTIEON_INSTALL_DIR=$sentieon_root
export PATH=$oracle_prefix/bin:$sentieon_root/bin:$PATH
export LD_PRELOAD=$oracle_prefix/lib/libjemalloc.so${LD_PRELOAD:+:$LD_PRELOAD}
export bwt_max_mem=180G
export MALLOC_CONF=background_thread:true,metadata_thp:auto,dirty_decay_ms:5000,muzzy_decay_ms:5000
ulimit -n 65536 || die "could not raise open-file limit"

cli=(
    env
    "PYTHONPATH=$source_checkout"
    "$oracle_prefix/bin/python"
    "$checkout_runner"
)
resolved_module=$(
    env "PYTHONPATH=$source_checkout" "$oracle_prefix/bin/python" -c \
        'import pathlib, sentieon_cli; print(pathlib.Path(sentieon_cli.__file__).resolve())'
)
expected_module=$(readlink -f "$source_checkout/sentieon_cli/__init__.py")
[[ $resolved_module == "$expected_module" ]] \
    || die "CLI imports $resolved_module, expected $expected_module"
cli_version=$("${cli[@]}" --version 2>&1)
[[ $cli_version == 1.7.0 ]] \
    || die "unexpected CLI version: $cli_version"
source_version=$(
    "$oracle_prefix/bin/python" -c \
        'import sys, tomllib; print(tomllib.load(open(sys.argv[1], "rb"))["project"]["version"])' \
        "$source_checkout/pyproject.toml"
)
[[ $source_version == "$expected_source_version" ]] \
    || die "unexpected source package version: $source_version"
genomics_version=$($sentieon_root/bin/sentieon driver --version 2>&1)
[[ $genomics_version == *"sentieon-genomics-202503.03"* ]] \
    || die "unexpected Sentieon version: $genomics_version"

scratch_parent=/scratch/sentieon-cli-171i-hg003-5x/$candidate-gvcf/$SLURM_JOB_ID
mkdir -p "$scratch_parent"
job_root=$(mktemp -d "$scratch_parent/job.XXXXXX")
case $job_root in
    "$scratch_parent"/job.*) ;;
    *) die "unexpected scratch directory: $job_root" ;;
esac
work=$job_root/work
tmp=$job_root/tmp
mkdir -p "$work" "$tmp"
export TMPDIR=$tmp
export TMP=$tmp
export TEMP=$tmp
export SENTIEON_TMPDIR=$tmp

published=0
cleanup() {
    rc=$?
    trap - EXIT INT TERM
    if (( published )); then
        rm -rf -- "$job_root"
        rmdir "$scratch_parent" 2>/dev/null || true
    else
        printf 'FAILED rc=%s; preserving NVMe evidence at %s\n' "$rc" "$job_root" >&2
    fi
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

output_gvcf=$work/$analysis_unit.sentieon-cli.g.vcf.gz
command=(
    "${cli[@]}" dnascope-hybrid
    --sr_aln "$sr_cram"
    --sr_duplicate_marking none
    --lr_aln "$lr_cram"
    --lr_input_ref "$reference"
    --rgsm "$analysis_unit"
    -r "$reference"
    -m "$model_bundle"
    -d "$dbsnp"
    --pop_vcf "$population_vcf"
    -b "$scope_bed"
    --skip_svs
    --skip_cnv
    --skip_metrics
    --skip_mosdepth
    --skip_multiqc
    -t "$SLURM_CPUS_PER_TASK"
    --gvcf
    "$output_gvcf"
)
{
    printf 'command='
    printf ' %q' "${command[@]}"
    printf '\n'
} > "$work/command.txt"

start_epoch=$(date +%s)
/usr/bin/time -v -o "$work/time.txt" "${command[@]}"
end_epoch=$(date +%s)

[[ -s $output_gvcf ]] || die "CLI did not produce $output_gvcf"
if [[ ! -s $output_gvcf.tbi ]]; then
    bcftools index --threads "$SLURM_CPUS_PER_TASK" --tbi --force "$output_gvcf"
fi
bgzip -t "$output_gvcf"
tabix -l "$output_gvcf" > "$work/contigs.txt"
bcftools query -l "$output_gvcf" > "$work/samples.txt"
record_count=$(bcftools index --nrecords "$output_gvcf")
[[ $record_count =~ ^[0-9]+$ && $record_count -gt 0 ]] \
    || die "invalid indexed record count: $record_count"

publish_parent=$(dirname "$publish_dir")
publish_basename=$(basename "$publish_dir")
mkdir -p "$publish_parent"
publish_stage=$(mktemp -d "$publish_parent/.${publish_basename}.publish.XXXXXX")
cp -p \
    "$output_gvcf" "$output_gvcf.tbi" \
    "$work/time.txt" "$work/command.txt" \
    "$work/contigs.txt" "$work/samples.txt" \
    "$publish_stage/"
{
    printf 'candidate=%s\n' "$candidate"
    printf 'source_repository=%s\n' "$source_repository"
    printf 'source_ref=%s\n' "$expected_tag"
    printf 'source_sha=%s\n' "$source_sha"
    printf 'resolved_module=%s\n' "$resolved_module"
    printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
    printf 'slurm_partition=%s\n' "$SLURM_JOB_PARTITION"
    printf 'slurm_cpus_per_task=%s\n' "$SLURM_CPUS_PER_TASK"
    printf 'start_epoch=%s\n' "$start_epoch"
    printf 'end_epoch=%s\n' "$end_epoch"
    printf 'wall_seconds=%s\n' "$((end_epoch - start_epoch))"
    printf 'sentieon_cli=%s\n' "$cli_version"
    printf 'source_package_version=%s\n' "$source_version"
    printf 'version_note=%s\n' \
        'PYTHONPATH source injection retains installed distribution metadata for --version'
    printf 'sentieon_genomics=%s\n' "$genomics_version"
    printf 'reference=%s\n' "$reference"
    printf 'model_bundle=%s\n' "$model_bundle"
    printf 'dbsnp=%s\n' "$dbsnp"
    printf 'population_vcf=%s\n' "$population_vcf"
    printf 'scope_bed=%s\n' "$scope_bed"
    printf 'scope_bed_sha256=%s\n' "$scope_sha"
    printf 'sr_cram=%s\n' "$sr_cram"
    printf 'lr_cram=%s\n' "$lr_cram"
    printf 'indexed_record_count=%s\n' "$record_count"
    sha256sum "$output_gvcf" "$output_gvcf.tbi"
} > "$publish_stage/run-manifest.txt"
printf 'status=SUCCESS\ncompleted_utc=%s\n' "$(date -u +%FT%TZ)" \
    > "$publish_stage/completion.receipt"
mv "$publish_stage" "$publish_dir"
published=1
printf 'Published completed %s gVCF result to %s\n' "$candidate" "$publish_dir"
