#!/usr/bin/env bash
#SBATCH --cpus-per-task=16
#SBATCH --partition=i128nvme
#SBATCH --time=04:00:00
#SBATCH --comment=RnD

set -euo pipefail

analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-4xvrg7erk7knfs
stamp=20260731T090232Z
evidence_root="${analysis_root}/manual/sentieon-cli-issue-evidence/${analysis_unit}/${stamp}"
bucket=lsmc-dayoa-analysis-results-usw2
prefix=validation/sentieon-cli/hg003-fullcov-hard-vs-gvcf-20260731

raw_gvcf="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/hybrid-cli170/${analysis_unit}.sentdhiomr2.hybrid-cli170.g.vcf.gz"
derived_hard="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/five-chromosome-shards/${analysis_unit}.sentdhiomr2.vcf.gz"
native_hard="${analysis_root}/manual/s170h/1767/${analysis_unit}.native-cli170-hard.vcf.gz"
derived_rtg_tar="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/concordance/_giabHC/rtg-vcfeval-scratch.tar"
raw_rtg="${analysis_root}/manual/rtg-three-way/${analysis_unit}/cli170_gvcf_raw_hc/1769"
native_rtg="${analysis_root}/manual/rtg-three-way/${analysis_unit}/cli170_native_hard_hc/1770"

for required in \
  "$raw_gvcf" "$raw_gvcf.tbi" \
  "$derived_hard" "$derived_hard.tbi" \
  "$native_hard" "$native_hard.tbi" \
  "$derived_rtg_tar" \
  "$raw_rtg/summary.txt" "$native_rtg/summary.txt" \
  "$evidence_root/full-coverage-evidence.receipt" \
  "$evidence_root/postprocess/completion.receipt" \
  "$evidence_root/control/comparison/completion.receipt" \
  "$evidence_root/control/final-verification/completion.receipt"
do
  [[ -s "$required" ]] || {
    printf 'required S3 evidence input is missing or empty: %s\n' "$required" >&2
    exit 2
  }
done
[[ ! -e "$evidence_root/s3-staging" ]] || {
  printf 'refusing to overwrite completed S3 staging\n' >&2
  exit 2
}

scratch_parent="/scratch/dayoa/sentieon-cli-evidence/${analysis_unit}/s3-export/${SLURM_JOB_ID}"
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
mkdir -p "$work"/{derived-rtg,metadata}
manifest="${work}/upload-manifest.tsv"
printf 'object_key\tsource_path\tsize_bytes\tsha256\n' > "$manifest"

tar -xf "$derived_rtg_tar" -C "$work/derived-rtg"

readme="${work}/README.md"
{
  printf '# HG003 Sentieon CLI 1.7.0 hard-vs-gVCF evidence\n\n'
  printf 'This private evidence set supports the public investigation of native '
  printf 'Hybrid hard-VCF output versus gVCF followed by GVCFtyper.\n\n'
  printf -- '- Analysis unit: `%s`\n' "$analysis_unit"
  printf -- '- Full-coverage source lanes: Slurm 1767, 1769, and 1770\n'
  printf -- '- Invalid Slurm 1768 lane: explicitly excluded\n'
  printf -- '- Sentieon CLI fork commit: `c7d9fd4ebad013ebc76052578e967f28d2e065e9`\n'
  printf -- '- Sentieon Genomics: `202503.03`\n'
  printf -- '- Evidence timestamp: `%s`\n\n' "$stamp"
  printf 'No reads, alignments, references, model bundles, licenses, credentials, '
  printf 'or retained CLI scratch trees are included.\n'
} > "$readme"

bundle="${work}/HG003-sentieon-cli-hard-vs-gvcf-evidence.tar.gz"
tar -czf "$bundle" \
  -C "$evidence_root" \
  headers inventory differences rtg provenance postprocess \
  control/comparison control/final-verification \
  full-coverage-evidence.receipt

add_file() {
  source_path=$1
  object_key=$2
  size="$(stat -c %s "$source_path")"
  sha="$(sha256sum "$source_path" | awk '{print $1}')"
  printf '%s\t%s\t%s\t%s\n' "$object_key" "$source_path" "$size" "$sha" \
    >> "$manifest"
}

add_file_as() {
  hash_source=$1
  durable_source=$2
  object_key=$3
  size="$(stat -c %s "$hash_source")"
  sha="$(sha256sum "$hash_source" | awk '{print $1}')"
  printf '%s\t%s\t%s\t%s\n' \
    "$object_key" "$durable_source" "$size" "$sha" >> "$manifest"
}

add_file "$raw_gvcf" "vcf/raw-cli-gvcf/$(basename "$raw_gvcf")"
add_file "$raw_gvcf.tbi" "vcf/raw-cli-gvcf/$(basename "$raw_gvcf.tbi")"
add_file "$derived_hard" "vcf/gvcftyper-derived-hard/$(basename "$derived_hard")"
add_file "$derived_hard.tbi" "vcf/gvcftyper-derived-hard/$(basename "$derived_hard.tbi")"
add_file "$native_hard" "vcf/native-cli-hard/$(basename "$native_hard")"
add_file "$native_hard.tbi" "vcf/native-cli-hard/$(basename "$native_hard.tbi")"

for lane_spec in \
  "raw-cli-gvcf|$raw_rtg" \
  "gvcftyper-derived-hard|$work/derived-rtg" \
  "native-cli-hard|$native_rtg"
do
  IFS='|' read -r lane lane_root <<< "$lane_spec"
  for name in summary.txt tp.vcf.gz tp.vcf.gz.tbi tp-baseline.vcf.gz \
    tp-baseline.vcf.gz.tbi fp.vcf.gz fp.vcf.gz.tbi fn.vcf.gz fn.vcf.gz.tbi
  do
    source_path="${lane_root}/${name}"
    [[ -s "$source_path" ]] || {
      printf 'missing RTG evidence: %s\n' "$source_path" >&2
      exit 2
    }
    add_file "$source_path" "rtg/${lane}/${name}"
  done
done

for evidence_dir in \
  headers inventory differences rtg provenance postprocess \
  control/comparison control/final-verification
do
  while IFS= read -r -d '' source_path; do
    relative="${source_path#${evidence_root}/}"
    add_file "$source_path" "evidence/${relative}"
  done < <(find "$evidence_root/$evidence_dir" -type f -print0)
done

staging="${evidence_root}/.publish-s3-staging-${SLURM_JOB_ID}"
final_staging="${evidence_root}/s3-staging"
[[ ! -e "$staging" ]] || {
  printf 'S3 staging path already exists: %s\n' "$staging" >&2
  exit 2
}
mkdir -p "$staging/derived-rtg"
cp "$readme" "$staging/README.md"
cp "$bundle" "$staging/$(basename "$bundle")"
for name in summary.txt tp.vcf.gz tp.vcf.gz.tbi tp-baseline.vcf.gz \
  tp-baseline.vcf.gz.tbi fp.vcf.gz fp.vcf.gz.tbi fn.vcf.gz fn.vcf.gz.tbi
do
  cp "$work/derived-rtg/$name" "$staging/derived-rtg/$name"
done

# Replace the ephemeral extracted-tar sources with the durable published
# staging copies before the presigned upload manifest leaves this job.
python3 - "$manifest" "$work/derived-rtg" "$final_staging/derived-rtg" <<'PY'
import csv
import pathlib
import sys

manifest = pathlib.Path(sys.argv[1])
ephemeral = str(pathlib.Path(sys.argv[2]))
durable = str(pathlib.Path(sys.argv[3]))
with manifest.open(newline="") as source:
    rows = list(csv.DictReader(source, delimiter="\t"))
with manifest.open("w", newline="") as output:
    writer = csv.DictWriter(
        output,
        fieldnames=("object_key", "source_path", "size_bytes", "sha256"),
        delimiter="\t",
        lineterminator="\n",
    )
    writer.writeheader()
    for row in rows:
        if row["source_path"].startswith(f"{ephemeral}/"):
            row["source_path"] = row["source_path"].replace(
                f"{ephemeral}/", f"{durable}/", 1
            )
        writer.writerow(row)
PY

add_file_as \
  "$staging/README.md" \
  "$final_staging/README.md" \
  README.md
add_file_as \
  "$staging/$(basename "$bundle")" \
  "$final_staging/$(basename "$bundle")" \
  "$(basename "$bundle")"

{
  printf 'object_key\tsize_bytes\tsha256\n'
  tail -n +2 "$manifest" |
    awk -F '\t' 'BEGIN {OFS="\t"} {print $1, $3, $4}'
} > "$staging/SHA256SUMS.tsv"
add_file_as \
  "$staging/SHA256SUMS.tsv" \
  "$final_staging/SHA256SUMS.tsv" \
  SHA256SUMS.tsv

manifest_sha="$(sha256sum "$manifest" | awk '{print $1}')"
cp "$manifest" "$staging/S3-upload-manifest.tsv"
{
  printf 'status=STAGED\n'
  printf 'completed_utc=%s\n' "$(date -u +%FT%TZ)"
  printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
  printf 's3_prefix=s3://%s/%s/\n' "$bucket" "$prefix"
  printf 'manifest_sha256=%s\n' "$manifest_sha"
  printf 'upload_authority=local-lsmc-presigned-put-required\n'
} > "$staging/s3-staging.receipt"
mv "$staging" "$final_staging"

printf 'staged=%s\ns3_prefix=s3://%s/%s/\ncompleted_utc=%s\n' \
  "$final_staging" "$bucket" "$prefix" "$(date -u +%FT%TZ)"
success=1
