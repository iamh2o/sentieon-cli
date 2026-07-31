#!/usr/bin/env bash
#SBATCH --cpus-per-task=1
#SBATCH --partition=i128nvme
#SBATCH --time=00:15:00
#SBATCH --comment=RnD

set -euo pipefail

analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-4xvrg7erk7knfs
stamp=20260731T090232Z
evidence_root="${analysis_root}/manual/sentieon-cli-issue-evidence/${analysis_unit}/${stamp}"
publish_root="${evidence_root}/provenance/rtg-runtime"
rtg=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/e1ff8841ae9cd380c0d64a16bcfd2861_/bin/rtg

for required in \
  "$rtg" \
  "$evidence_root/provenance/raw-gvcf-rtg-command.txt" \
  "$evidence_root/provenance/native-hard-rtg-command.txt"
do
  [[ -s "$required" ]] || {
    printf 'required RTG provenance input is missing or empty: %s\n' \
      "$required" >&2
    exit 2
  }
done
[[ ! -e "$publish_root" ]] || {
  printf 'refusing to overwrite RTG runtime provenance: %s\n' \
    "$publish_root" >&2
  exit 2
}

staging="${evidence_root}/.publish-rtg-runtime-${SLURM_JOB_ID}"
mkdir "$staging"
"$rtg" version > "$staging/rtg-version.txt"
{
  printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
  printf 'node=%s\n' "$(hostname)"
  printf 'collected_utc=%s\n' "$(date -u +%FT%TZ)"
} > "$staging/job.txt"
(
  cd "$staging"
  sha256sum rtg-version.txt job.txt
) > "$staging/SHA256SUMS"
mv "$staging" "$publish_root"
printf 'published=%s\n' "$publish_root"
