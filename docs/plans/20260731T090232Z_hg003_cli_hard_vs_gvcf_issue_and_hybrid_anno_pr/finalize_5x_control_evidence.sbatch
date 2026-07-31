#!/usr/bin/env bash
#SBATCH --cpus-per-task=16
#SBATCH --partition=i128nvme
#SBATCH --time=02:00:00
#SBATCH --comment=RnD

set -euo pipefail

analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-SR5X-ONT5X-SENTCLI-CONTROL
stamp=20260731T090232Z
evidence_root="${analysis_root}/manual/sentieon-cli-issue-evidence/HG003-4xvrg7erk7knfs/${stamp}"
control_root="${evidence_root}/control"
result_root="${control_root}/results"
comparison_root="${control_root}/comparison"
source_root="${control_root}/sources"
publish_root="${control_root}/final-verification"

hts_env=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/c5cd8e2ced5dbe136787cd01ea6028d5_
bcftools="${hts_env}/bin/bcftools"
bgzip="${hts_env}/bin/bgzip"
tabix="${hts_env}/bin/tabix"

upstream_hard="${result_root}/upstream/hard/${analysis_unit}.upstream.native-hard.vcf.gz"
optimized_hard="${result_root}/optimized/hard/${analysis_unit}.optimized.native-hard.vcf.gz"
upstream_gvcf="${result_root}/upstream/gvcf/${analysis_unit}.upstream.g.vcf.gz"
optimized_gvcf="${result_root}/optimized/gvcf/${analysis_unit}.optimized.g.vcf.gz"
upstream_derived="${result_root}/upstream/gvcf/${analysis_unit}.upstream.from-gvcf.hard.vcf.gz"
optimized_derived="${result_root}/optimized/gvcf/${analysis_unit}.optimized.from-gvcf.hard.vcf.gz"
annotation_input="${result_root}/upstream/hard/retained-cli-tmp/combined_tmp.vcf.gz"
annotation_bed="${result_root}/upstream/hard/retained-cli-tmp/stage1_hap.bed"
upstream_anno="${source_root}/upstream-v1.7.0/sentieon_cli/scripts/hybrid_anno.py"
optimized_anno="${source_root}/optimized-v1.7.0/sentieon_cli/scripts/hybrid_anno.py"

for required in \
  "$bcftools" "$bgzip" "$tabix" \
  "$comparison_root/completion.receipt" \
  "$comparison_root/performance/summary.tsv" \
  "$comparison_root/rtg/matched-mode-equivalence.tsv" \
  "$annotation_input" "$annotation_input.tbi" "$annotation_bed" \
  "$upstream_anno" "$optimized_anno" \
  "$upstream_hard" "$upstream_hard.tbi" \
  "$optimized_hard" "$optimized_hard.tbi" \
  "$upstream_gvcf" "$upstream_gvcf.tbi" \
  "$optimized_gvcf" "$optimized_gvcf.tbi" \
  "$upstream_derived" "$upstream_derived.tbi" \
  "$optimized_derived" "$optimized_derived.tbi"
do
  [[ -s "$required" ]] || {
    printf 'required final-verification input is missing or empty: %s\n' \
      "$required" >&2
    exit 2
  }
done
[[ ! -e "$publish_root" ]] || {
  printf 'refusing to overwrite control final verification: %s\n' \
    "$publish_root" >&2
  exit 2
}

scratch_parent="/scratch/dayoa/sentieon-cli-control/${analysis_unit}/final-verification/${SLURM_JOB_ID}"
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

result="${job_root}/result"
mkdir -p "$result"

printf 'lane\trecord_count\tsample\tbgzip_valid\ttabix_contigs\n' \
  > "$result/product-verification.tsv"
for lane_spec in \
  "upstream-native|$upstream_hard" \
  "optimized-native|$optimized_hard" \
  "upstream-gvcf|$upstream_gvcf" \
  "optimized-gvcf|$optimized_gvcf" \
  "upstream-from-gvcf|$upstream_derived" \
  "optimized-from-gvcf|$optimized_derived"
do
  IFS='|' read -r lane input_vcf <<< "$lane_spec"
  "$bgzip" -t "$input_vcf"
  sample="$("$bcftools" query -l "$input_vcf")"
  [[ "$sample" == "$analysis_unit" ]] || {
    printf 'unexpected sample for %s: %s\n' "$lane" "$sample" >&2
    exit 1
  }
  record_count="$("$bcftools" view -H "$input_vcf" | wc -l)"
  contig_count="$("$tabix" -l "$input_vcf" | wc -l)"
  printf '%s\t%s\t%s\ttrue\t%s\n' \
    "$lane" "$record_count" "$sample" "$contig_count" \
    >> "$result/product-verification.tsv"
done

upstream_input_records="$("$bcftools" view -H "$annotation_input" | wc -l)"
{
  printf 'requested_threads=128\n'
  printf 'annotation_input=%s\n' "$annotation_input"
  printf 'annotation_input_records=%s\n' "$upstream_input_records"
  printf 'annotation_bed=%s\n' "$annotation_bed"
  printf 'annotation_bed_sha256=%s\n' \
    "$(sha256sum "$annotation_bed" | awk '{print $1}')"
  printf 'upstream_script=%s\n' "$upstream_anno"
  printf 'upstream_script_sha256=%s\n' \
    "$(sha256sum "$upstream_anno" | awk '{print $1}')"
  printf 'optimized_script=%s\n' "$optimized_anno"
  printf 'optimized_script_sha256=%s\n' \
    "$(sha256sum "$optimized_anno" | awk '{print $1}')"
  printf 'interface=hybrid_anno.py -v INPUT -b stage1_hap.bed -t 128 OUTPUT\n'
} > "$result/annotation-command-and-record-provenance.txt"

for lane in upstream/hard upstream/gvcf optimized/hard optimized/gvcf; do
  cp \
    "$result_root/$lane/command-resource-provenance.txt" \
    "$result/$(tr / - <<< "$lane").command-resource-provenance.txt"
done

python3 - "$comparison_root/performance/summary.tsv" <<'PY'
import pathlib
import sys

lines = pathlib.Path(sys.argv[1]).read_text().splitlines()
reductions = [
    float(line.split("\t", 1)[1])
    for line in lines
    if line.startswith("wall_time_reduction_percent\t")
]
if reductions != reductions[:1] or not reductions or reductions[0] < 90.0:
    raise SystemExit(f"invalid or insufficient performance reduction: {reductions}")
PY

cp \
  "$comparison_root/performance/summary.tsv" \
  "$comparison_root/semantic/matched-mode-hashes.tsv" \
  "$comparison_root/semantic/upstream-mode-distinction.txt" \
  "$comparison_root/rtg/matched-mode-equivalence.tsv" \
  "$comparison_root/rtg/upstream-mode-summary.diff" \
  "$result/"

(
  cd "$result"
  find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
) > "$result/SHA256SUMS"

staging="${control_root}/.publish-final-verification-${SLURM_JOB_ID}"
mkdir "$staging"
cp -a "$result/." "$staging/"
printf 'status=SUCCESS\ncompleted_utc=%s\nslurm_job_id=%s\n' \
  "$(date -u +%FT%TZ)" "$SLURM_JOB_ID" \
  > "$staging/completion.receipt"
mv "$staging" "$publish_root"
printf 'published=%s\n' "$publish_root"
success=1
