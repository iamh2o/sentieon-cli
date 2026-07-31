#!/usr/bin/env bash
#SBATCH --cpus-per-task=16
#SBATCH --partition=i128nvme
#SBATCH --time=06:00:00
#SBATCH --comment=RnD

set -euo pipefail

put_manifest="${1:?presigned PUT manifest path is required}"
analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-4xvrg7erk7knfs
stamp=20260731T090232Z
evidence_root="${analysis_root}/manual/sentieon-cli-issue-evidence/${analysis_unit}/${stamp}"
receipt_root="${evidence_root}/s3-staging"

[[ -s "$put_manifest" ]] || {
  printf 'presigned PUT manifest is missing or empty: %s\n' "$put_manifest" >&2
  exit 2
}
[[ -s "$receipt_root/s3-staging.receipt" ]] || {
  printf 'S3 evidence staging receipt is missing\n' >&2
  exit 2
}
[[ ! -e "$receipt_root/s3-upload.receipt" ]] || {
  printf 'refusing to repeat completed S3 upload\n' >&2
  exit 2
}

scratch_parent="/scratch/dayoa/sentieon-cli-evidence/${analysis_unit}/presigned-upload/${SLURM_JOB_ID}"
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

receipt="${job_root}/s3-upload-receipt.tsv"
printf 'object_key\tsize_bytes\tsha256\thttp_code\tstatus\n' > "$receipt"

{
  IFS= read -r header
  [[ "$header" == $'object_key\tsource_path\tsize_bytes\tsha256\tput_url' ]] || {
    printf 'unexpected PUT manifest header\n' >&2
    exit 2
  }
  while IFS=$'\t' read -r object_key source_path expected_size expected_sha put_url
  do
    [[ -s "$source_path" ]] || {
      printf 'upload source is missing or empty: %s\n' "$source_path" >&2
      exit 2
    }
    observed_size="$(stat -c %s "$source_path")"
    [[ "$observed_size" == "$expected_size" ]] || {
      printf 'upload source size changed: %s\n' "$source_path" >&2
      exit 2
    }
    [[ "$observed_size" -le 5368709120 ]] || {
      printf 'single PUT object exceeds 5 GiB: %s\n' "$source_path" >&2
      exit 2
    }
    observed_sha="$(sha256sum "$source_path" | awk '{print $1}')"
    [[ "$observed_sha" == "$expected_sha" ]] || {
      printf 'upload source checksum changed: %s\n' "$source_path" >&2
      exit 2
    }
    printf 'uploading object=%s size=%s\n' "$object_key" "$observed_size"
    http_code="$(
      curl \
        --fail \
        --silent \
        --show-error \
        --retry 3 \
        --retry-all-errors \
        --output /dev/null \
        --write-out '%{http_code}' \
        --header "x-amz-meta-sha256: ${observed_sha}" \
        --upload-file "$source_path" \
        "$put_url"
    )"
    [[ "$http_code" == 200 ]] || {
      printf 'S3 PUT returned HTTP %s for %s\n' "$http_code" "$object_key" >&2
      exit 1
    }
    printf '%s\t%s\t%s\t%s\tSUCCESS\n' \
      "$object_key" "$observed_size" "$observed_sha" "$http_code" \
      >> "$receipt"
  done
} < "$put_manifest"

cp "$receipt" "$receipt_root/s3-upload-receipt.tsv"
{
  printf 'status=UPLOADED_AWAITING_LOCAL_VERIFICATION\n'
  printf 'completed_utc=%s\n' "$(date -u +%FT%TZ)"
  printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
} > "$receipt_root/s3-upload.receipt"
printf 'uploaded_utc=%s\n' "$(date -u +%FT%TZ)"
success=1
