#!/usr/bin/env bash
#SBATCH --cpus-per-task=128
#SBATCH --partition=i128nvme
#SBATCH --time=12:00:00
#SBATCH --comment=RnD

set -euo pipefail

implementation="${1:?implementation is required: upstream or optimized}"
mode="${2:?mode is required: hard or gvcf}"
case "$implementation" in
  upstream|optimized) ;;
  *) printf 'invalid implementation: %s\n' "$implementation" >&2; exit 2 ;;
esac
case "$mode" in
  hard|gvcf) ;;
  *) printf 'invalid mode: %s\n' "$mode" >&2; exit 2 ;;
esac

threads="${SLURM_CPUS_PER_TASK:?SLURM_CPUS_PER_TASK is required}"
[[ "$threads" == 128 ]] || {
  printf 'expected exactly 128 allocated CPUs, received %s\n' "$threads" >&2
  exit 2
}

analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-SR5X-ONT5X-SENTCLI-CONTROL
stamp=20260731T090232Z
evidence_root="${analysis_root}/manual/sentieon-cli-issue-evidence/HG003-4xvrg7erk7knfs/${stamp}"
source_root="${evidence_root}/control/sources"
publish_root="${evidence_root}/control/results/${implementation}/${mode}"

runtime_root=/fsx/analysis_results/preval-hiomr2/cli-comparison/comparison/runtime/sentieon-cli-1.7.0
runtime_python="${runtime_root}/venv/bin/python"
env_prefix=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/c5cd8e2ced5dbe136787cd01ea6028d5_
sentieon_root=/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.03

sr_r1=/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/NovaSeqX_WHGS_TruSeqPF_HG002-007/downsampled/HG003_5x_R1.fastq.gz
sr_r2=/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/NovaSeqX_WHGS_TruSeqPF_HG002-007/downsampled/HG003_5x_R2.fastq.gz
lr_fastq=/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/agbt_2026/ont/HG003_5x.cleaned.primary.fastq.gz
reference=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/fasta_fai_minalt/GRCh38_no_alt_analysis_set.fasta
model=/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.03/bundles/HybridIlluminaONT2.0.bundle
dbsnp=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/gatk/Homo_sapiens_assembly38.dbsnp138.vcf.gz
population_vcf=/fsx/references/genomic_data/organism_references/H_sapiens/panhg38/pop-v20g41-20251216.vcf.gz
scope_bed=/fsx/analysis_results/preval-hiomr2/cli-comparison/comparison/scope/chr1-chr22-X-Y-M.fullgenome.scope.bed

if [[ "$implementation" == upstream ]]; then
  checkout="${source_root}/upstream-v1.7.0"
  required_commit=1bf377d3ce79fc4d8c2dc221e1f696441e38349d
else
  checkout="${source_root}/optimized-v1.7.0"
  required_commit=c7d9fd4ebad013ebc76052578e967f28d2e065e9
fi

for required in \
  "$runtime_python" \
  "$env_prefix/bin/samtools" \
  "$env_prefix/bin/bcftools" \
  "$env_prefix/bin/bgzip" \
  "$env_prefix/bin/tabix" \
  "$sentieon_root/bin/sentieon" \
  "$checkout/sentieon_cli/scripts/hybrid_anno.py" \
  "$sr_r1" "$sr_r2" "$lr_fastq" \
  "$reference" "$reference.fai" \
  "$model" "$dbsnp" "$dbsnp.tbi" \
  "$population_vcf" "$population_vcf.tbi" "$scope_bed"
do
  [[ -s "$required" ]] || {
    printf 'required input is missing or empty: %s\n' "$required" >&2
    exit 2
  }
done

observed_commit="$(git -C "$checkout" rev-parse HEAD)"
observed_status="$(git -C "$checkout" status --porcelain)"
[[ "$observed_commit" == "$required_commit" ]] || {
  printf 'source checkout mismatch: expected %s, observed %s\n' \
    "$required_commit" "$observed_commit" >&2
  exit 2
}
[[ -z "$observed_status" ]] || {
  printf 'source checkout is dirty:\n%s\n' "$observed_status" >&2
  exit 2
}

if [[ -e "$publish_root" ]]; then
  printf 'refusing to overwrite control result: %s\n' "$publish_root" >&2
  exit 2
fi

scratch_parent="/scratch/dayoa/sentieon-cli-control/${analysis_unit}/${implementation}/${mode}/${SLURM_JOB_ID}"
mkdir -p "$scratch_parent"
job_root="$(mktemp -d "${scratch_parent}/job.XXXXXX")"
case "$job_root" in
  "$scratch_parent"/job.*) ;;
  *) printf 'unexpected scratch directory: %s\n' "$job_root" >&2; exit 2 ;;
esac

success=0
cleanup() {
  status=$?
  if [[ $success == 1 ]]; then
    rm -rf -- "$job_root"
  else
    printf 'preserved failed scratch root: %s\n' "$job_root" >&2
  fi
  exit "$status"
}
trap cleanup EXIT

work="${job_root}/work"
sentieon_tmp_base="${job_root}/sentieon-tmp"
mkdir -p "$work" "$sentieon_tmp_base"
export TMPDIR="${job_root}/tmp"
export SENTIEON_TMPDIR="$sentieon_tmp_base"
export PYTHONPATH="$checkout"
export PATH="$sentieon_root/bin:$env_prefix/bin:/usr/bin:/bin"
mkdir -p "$TMPDIR"

loaded_package="$(
  "$runtime_python" -c \
    'import pathlib, sentieon_cli; print(pathlib.Path(sentieon_cli.__file__).resolve())'
)"
expected_package="$checkout/sentieon_cli/__init__.py"
[[ "$loaded_package" == "$expected_package" ]] || {
  printf 'requested source package was not loaded: %s\n' "$loaded_package" >&2
  exit 2
}

lr_ubam="${work}/${analysis_unit}-lr.input.ubam"
sr_readgroups='@RG\tID:HG003-SR5X-ONT5X-SENTCLI-CONTROL-sr\tSM:HG003-SR5X-ONT5X-SENTCLI-CONTROL'
lr_readgroups=$'@RG\tID:HG003-SR5X-ONT5X-SENTCLI-CONTROL-lr\tSM:HG003-SR5X-ONT5X-SENTCLI-CONTROL'

if [[ "$mode" == hard ]]; then
  primary_name="${analysis_unit}.${implementation}.native-hard.vcf.gz"
  mode_args=()
else
  primary_name="${analysis_unit}.${implementation}.g.vcf.gz"
  mode_args=(--gvcf)
fi
local_primary="${work}/${primary_name}"

printf 'started_utc=%s\nimplementation=%s\nmode=%s\nslurm_job_id=%s\nnode=%s\n' \
  "$(date -u +%FT%TZ)" "$implementation" "$mode" "$SLURM_JOB_ID" "$(hostname)"

printf 'samtools_import='
printf '%q ' "$env_prefix/bin/samtools" import -@ "$threads" \
  -r "$lr_readgroups" -0 "$lr_fastq" -O BAM -o "$lr_ubam"
printf '\n'
"$env_prefix/bin/samtools" import -@ "$threads" \
  -r "$lr_readgroups" -0 "$lr_fastq" -O BAM -o "$lr_ubam"

cli_command=(
  "$runtime_python"
  -c "from sentieon_cli import main; main()"
  dnascope-hybrid
  --sr_r1_fastq "$sr_r1"
  --sr_r2_fastq "$sr_r2"
  --sr_readgroups "$sr_readgroups"
  --lr_aln "$lr_ubam"
  --lr_align_input
  -r "$reference"
  -m "$model"
  -d "$dbsnp"
  --pop_vcf "$population_vcf"
  -b "$scope_bed"
  --rgsm "$analysis_unit"
  --sr_duplicate_marking markdup
  --skip_svs
  --skip_cnv
  --skip_metrics
  --skip_mosdepth
  --skip_multiqc
  --retain_tmpdir
  -t "$threads"
  "${mode_args[@]}"
  "$local_primary"
)

printf 'cli_command='
printf '%q ' "${cli_command[@]}"
printf '\n'
cli_started_epoch="$(date +%s)"
"${cli_command[@]}"
cli_finished_epoch="$(date +%s)"
cli_wall_seconds="$((cli_finished_epoch - cli_started_epoch))"

"$env_prefix/bin/bgzip" -t "$local_primary"
"$env_prefix/bin/tabix" -l "$local_primary" > "$work/primary.contigs.txt"
"$env_prefix/bin/bcftools" query -l "$local_primary" > "$work/primary.samples.txt"

derived_hard=
if [[ "$mode" == gvcf ]]; then
  raw_hard="${work}/${analysis_unit}.${implementation}.from-gvcf.raw.vcf.gz"
  derived_hard="${work}/${analysis_unit}.${implementation}.from-gvcf.hard.vcf.gz"
  gvcftyper_command=(
    "$sentieon_root/bin/sentieon"
    driver
    -r "$reference"
    -t "$threads"
    --algo GVCFtyper
    -d "$dbsnp"
    --emit_mode variant
    "$local_primary"
    "$raw_hard"
  )
  printf 'gvcftyper_command='
  printf '%q ' "${gvcftyper_command[@]}"
  printf '\n'
  "${gvcftyper_command[@]}"
  "$env_prefix/bin/bcftools" sort \
    -T "${job_root}/gvcftyper-sort" \
    -Oz -o "$derived_hard" "$raw_hard"
  "$env_prefix/bin/tabix" -f -p vcf "$derived_hard"
  "$env_prefix/bin/bgzip" -t "$derived_hard"
fi

retained_children=("$sentieon_tmp_base"/*)
[[ ${#retained_children[@]} -eq 1 && -d "${retained_children[0]}" ]] || {
  printf 'expected one retained Sentieon tmp directory, found %s\n' \
    "${#retained_children[@]}" >&2
  exit 2
}
retained_dir="${retained_children[0]}"
for retained_input in \
  "$retained_dir/combined_tmp.vcf.gz" \
  "$retained_dir/combined_tmp.vcf.gz.tbi" \
  "$retained_dir/stage1_hap.bed"
do
  [[ -s "$retained_input" ]] || {
    printf 'missing retained annotation input: %s\n' "$retained_input" >&2
    exit 2
  }
done

manifest="${work}/command-resource-provenance.txt"
{
  printf 'analysis_unit=%s\n' "$analysis_unit"
  printf 'implementation=%s\n' "$implementation"
  printf 'mode=%s\n' "$mode"
  printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
  printf 'slurm_partition=%s\n' "$SLURM_JOB_PARTITION"
  printf 'slurm_cpus_per_task=%s\n' "$threads"
  printf 'source_checkout=%s\n' "$checkout"
  printf 'source_commit=%s\n' "$observed_commit"
  printf 'hybrid_anno_sha256=%s\n' \
    "$(sha256sum "$checkout/sentieon_cli/scripts/hybrid_anno.py" | awk '{print $1}')"
  printf 'loaded_package=%s\n' "$loaded_package"
  printf 'sentieon_cli_version=%s\n' \
    "$("$runtime_python" -c 'import sentieon_cli; print(sentieon_cli.__version__)')"
  printf 'sentieon_genomics=202503.03\n'
  printf 'reference=%s\nmodel=%s\ndbsnp=%s\npopulation_vcf=%s\nscope_bed=%s\n' \
    "$reference" "$model" "$dbsnp" "$population_vcf" "$scope_bed"
  printf 'scope_bed_sha256=%s\n' "$(sha256sum "$scope_bed" | awk '{print $1}')"
  printf 'sr_r1=%s\nsr_r2=%s\nlr_fastq=%s\n' "$sr_r1" "$sr_r2" "$lr_fastq"
  printf 'cli_wall_seconds=%s\n' "$cli_wall_seconds"
  printf 'cli_command='
  printf '%q ' "${cli_command[@]}"
  printf '\n'
  if [[ "$mode" == gvcf ]]; then
    printf 'gvcftyper_command='
    printf '%q ' "${gvcftyper_command[@]}"
    printf '\n'
  fi
} > "$manifest"

staging="${evidence_root}/control/results/.publish-${implementation}-${mode}-${SLURM_JOB_ID}"
[[ ! -e "$staging" ]] || {
  printf 'staging directory already exists: %s\n' "$staging" >&2
  exit 2
}
mkdir -p "$staging/retained-cli-tmp"
cp "$local_primary" "$local_primary.tbi" "$staging/"
if [[ "$mode" == gvcf ]]; then
  cp "$derived_hard" "$derived_hard.tbi" "$staging/"
fi
cp "$manifest" "$work/primary.contigs.txt" "$work/primary.samples.txt" "$staging/"
cp -a "$retained_dir/." "$staging/retained-cli-tmp/"
(
  cd "$staging"
  find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
) > "$staging/SHA256SUMS"
printf 'status=SUCCESS\ncompleted_utc=%s\nslurm_job_id=%s\ncli_wall_seconds=%s\n' \
  "$(date -u +%FT%TZ)" "$SLURM_JOB_ID" "$cli_wall_seconds" \
  > "$staging/completion.receipt"

mkdir -p "$(dirname "$publish_root")"
mv "$staging" "$publish_root"
printf 'published=%s\ncompleted_utc=%s\n' \
  "$publish_root" "$(date -u +%FT%TZ)"
success=1
