#!/usr/bin/env bash
# Run the exact upstream Sentieon CLI v1.7.0 source as the HG003 hard-VCF
# baseline. Submit only with:
#   sbatch --partition i128nvme --comment RnD --cpus-per-task=128 ... \
#     ./run_hg003_official170_hard_core.sbatch <analysis-root> \
#     <official-v1.7.0-checkout>

set -euo pipefail

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

[[ $# -eq 2 ]] \
    || die "usage: $0 <analysis-root> <official-v1.7.0-checkout>"
analysis_root=$1
source_checkout=$2
expected_root=/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x
[[ $analysis_root == "$expected_root" ]] \
    || die "unexpected analysis root: $analysis_root"
[[ ${SLURM_JOB_ID-} =~ ^[0-9]+$ ]] || die "run this payload through sbatch"
[[ ${SLURM_CPUS_PER_TASK-} == 128 ]] \
    || die "requires --cpus-per-task=128"
[[ ${SLURM_JOB_PARTITION-} == i128nvme ]] \
    || die "requires --partition=i128nvme"

official_sha=1bf377d3ce79fc4d8c2dc221e1f696441e38349d
oracle_prefix=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/720569eabf1f3dc6300b2b50526585ed_
sentieon_root=/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.03
reference=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/fasta_fai_minalt/GRCh38_no_alt_analysis_set.fasta
model_bundle=$sentieon_root/bundles/HybridIlluminaONT2.0.bundle
dbsnp=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/gatk/Homo_sapiens_assembly38.dbsnp138.vcf.gz
population_vcf=/fsx/references/genomic_data/organism_references/H_sapiens/panhg38/pop-v20g41-20251216.vcf.gz
scope_bed=$analysis_root/inputs/full-primary.bed
expected_scope_sha=6f6179a3bc159e9527a56e665f8e5363fb8ee4af58696fbbdd043d1e0df6128d
prepared_dir=$analysis_root/prepared
analysis_unit=HG003-5X-CLI-RUNTIME
sr_cram=$prepared_dir/$analysis_unit.sr.prepared.cram
lr_cram=$prepared_dir/$analysis_unit.lr.aligned.cram
publish_dir=$analysis_root/results/official170/hard

[[ ! -e $publish_dir ]] \
    || die "publish destination already exists: $publish_dir"
[[ -d $source_checkout/.git || -f $source_checkout/.git ]] \
    || die "official source path is not a Git checkout: $source_checkout"
source_sha=$(git -C "$source_checkout" rev-parse HEAD)
[[ $source_sha == "$official_sha" ]] \
    || die "official checkout is $source_sha, expected $official_sha"
[[ -z $(git -C "$source_checkout" status --porcelain) ]] \
    || die "official v1.7.0 checkout is dirty"
tag_sha=$(git -C "$source_checkout" rev-parse 'v1.7.0^{}')
[[ $tag_sha == "$official_sha" ]] \
    || die "v1.7.0 resolves to $tag_sha, expected $official_sha"

for input_path in \
    "$reference" "$reference.fai" "$model_bundle" "$dbsnp" "$dbsnp.tbi" \
    "$population_vcf" "$population_vcf.tbi" "$scope_bed" "$sr_cram" \
    "$sr_cram.crai" "$lr_cram" "$lr_cram.crai" \
    "$oracle_prefix/bin/sentieon-cli"
do
    [[ -e $input_path ]] || die "required input/tool is missing: $input_path"
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

cli=(env "PYTHONPATH=$source_checkout" "$oracle_prefix/bin/sentieon-cli")
resolved_module=$(
    env "PYTHONPATH=$source_checkout" "$oracle_prefix/bin/python" -c \
        'import pathlib, sentieon_cli; print(pathlib.Path(sentieon_cli.__file__).resolve())'
)
expected_module=$(readlink -f "$source_checkout/sentieon_cli/__init__.py")
[[ $resolved_module == "$expected_module" ]] \
    || die "CLI imports $resolved_module, expected $expected_module"
cli_version=$("${cli[@]}" --version 2>&1)
[[ $cli_version == "1.7.0" ]] || die "unexpected CLI version: $cli_version"
genomics_version=$($sentieon_root/bin/sentieon driver --version 2>&1)
[[ $genomics_version == *"sentieon-genomics-202503.03"* ]] \
    || die "unexpected Sentieon version: $genomics_version"

scratch_parent=/scratch/sentieon-cli-171i-hg003-5x/official170/$SLURM_JOB_ID
mkdir -p "$scratch_parent"
job_root=$(mktemp -d "$scratch_parent/job.XXXXXX")
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
        printf 'FAILED rc=%s; preserving NVMe evidence at %s\n' \
            "$rc" "$job_root" >&2
    fi
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

output_vcf=$work/$analysis_unit.sentieon-cli.hard.vcf.gz
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
    --skip_metrics
    -t "$SLURM_CPUS_PER_TASK"
    "$output_vcf"
)
{
    printf 'command='
    printf ' %q' "${command[@]}"
    printf '\n'
} > "$work/command.txt"

start_epoch=$(date +%s)
/usr/bin/time -v -o "$work/time.txt" "${command[@]}"
end_epoch=$(date +%s)

output_stem=${output_vcf%.vcf.gz}
sv_vcf=$output_stem.sv.vcf.gz
cnv_vcf=$output_stem.cnv.vcf.gz
for variant_vcf in "$output_vcf" "$sv_vcf" "$cnv_vcf"; do
    [[ -s $variant_vcf ]] || die "CLI did not produce $variant_vcf"
    [[ -s $variant_vcf.tbi ]] || tabix -f -p vcf "$variant_vcf"
    bgzip -t "$variant_vcf"
    tabix -l "$variant_vcf" >/dev/null
    bcftools view -h "$variant_vcf" >/dev/null
done

publish_parent=$(dirname "$publish_dir")
publish_basename=$(basename "$publish_dir")
mkdir -p "$publish_parent"
publish_stage=$(mktemp -d "$publish_parent/.${publish_basename}.publish.XXXXXX")
cp -p \
    "$output_vcf" "$output_vcf.tbi" \
    "$sv_vcf" "$sv_vcf.tbi" \
    "$cnv_vcf" "$cnv_vcf.tbi" \
    "$work/time.txt" "$work/command.txt" "$publish_stage/"
{
    printf 'candidate=official170\n'
    printf 'source_repository=https://github.com/Sentieon/sentieon-cli.git\n'
    printf 'source_ref=v1.7.0\n'
    printf 'source_sha=%s\n' "$source_sha"
    printf 'resolved_module=%s\n' "$resolved_module"
    printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
    printf 'slurm_partition=%s\n' "$SLURM_JOB_PARTITION"
    printf 'slurm_cpus_per_task=%s\n' "$SLURM_CPUS_PER_TASK"
    printf 'start_epoch=%s\n' "$start_epoch"
    printf 'end_epoch=%s\n' "$end_epoch"
    printf 'wall_seconds=%s\n' "$((end_epoch - start_epoch))"
    printf 'sentieon_cli=%s\n' "$cli_version"
    printf 'sentieon_genomics=%s\n' "$genomics_version"
    printf 'reference=%s\n' "$reference"
    printf 'model_bundle=%s\n' "$model_bundle"
    printf 'dbsnp=%s\n' "$dbsnp"
    printf 'population_vcf=%s\n' "$population_vcf"
    printf 'scope_bed=%s\n' "$scope_bed"
    printf 'scope_bed_sha256=%s\n' "$scope_sha"
    printf 'sr_cram=%s\n' "$sr_cram"
    printf 'lr_cram=%s\n' "$lr_cram"
    sha256sum "$output_vcf" "$sv_vcf" "$cnv_vcf"
} > "$publish_stage/run-manifest.txt"
mv "$publish_stage" "$publish_dir"
published=1
printf 'Published completed official v1.7.0 result to %s\n' "$publish_dir"
