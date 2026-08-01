#!/usr/bin/env bash
#SBATCH --cpus-per-task=128
#SBATCH --partition=i128nvme
#SBATCH --time=08:00:00
#SBATCH --comment=RnD

set -euo pipefail

threads="${SLURM_CPUS_PER_TASK:?SLURM_CPUS_PER_TASK is required}"
[[ "$threads" == 128 ]] || {
  printf 'expected exactly 128 allocated CPUs, received %s\n' "$threads" >&2
  exit 2
}

analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-SR5X-ONT5X-SENTCLI-CONTROL
stamp=20260731T090232Z
evidence_root="${analysis_root}/manual/sentieon-cli-issue-evidence/HG003-4xvrg7erk7knfs/${stamp}"
control_root="${evidence_root}/control"
result_root="${control_root}/results"
source_root="${control_root}/sources"
publish_root="${control_root}/comparison"

runtime_python=/fsx/analysis_results/preval-hiomr2/cli-comparison/comparison/runtime/sentieon-cli-1.7.0/venv/bin/python
hts_env=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/c5cd8e2ced5dbe136787cd01ea6028d5_
rtg_env=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/e1ff8841ae9cd380c0d64a16bcfd2861_
reference=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/fasta_fai_minalt/GRCh38_no_alt_analysis_set.fasta
reference_sdf="${reference}.sdf"
truth=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/controls/giab/snv/v4.2.1/HG003/giabHC/HG003.vcf.gz
truth_bed=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/controls/giab/snv/v4.2.1/HG003/giabHC/HG003.bed

upstream_hard="${result_root}/upstream/hard/${analysis_unit}.upstream.native-hard.vcf.gz"
optimized_hard="${result_root}/optimized/hard/${analysis_unit}.optimized.native-hard.vcf.gz"
upstream_gvcf="${result_root}/upstream/gvcf/${analysis_unit}.upstream.g.vcf.gz"
optimized_gvcf="${result_root}/optimized/gvcf/${analysis_unit}.optimized.g.vcf.gz"
upstream_derived="${result_root}/upstream/gvcf/${analysis_unit}.upstream.from-gvcf.hard.vcf.gz"
optimized_derived="${result_root}/optimized/gvcf/${analysis_unit}.optimized.from-gvcf.hard.vcf.gz"

upstream_tmp="${result_root}/upstream/hard/retained-cli-tmp"
upstream_anno="${source_root}/upstream-v1.7.0/sentieon_cli/scripts/hybrid_anno.py"
optimized_anno="${source_root}/optimized-v1.7.0/sentieon_cli/scripts/hybrid_anno.py"
anno_input="${upstream_tmp}/combined_tmp.vcf.gz"
anno_bed="${upstream_tmp}/stage1_hap.bed"

bcftools="${hts_env}/bin/bcftools"
bgzip="${hts_env}/bin/bgzip"
tabix="${hts_env}/bin/tabix"
rtg="${rtg_env}/bin/rtg"

for required in \
  "$runtime_python" "$bcftools" "$bgzip" "$tabix" "$rtg" \
  "$reference" "$reference.fai" "$reference_sdf" \
  "$truth" "$truth.tbi" "$truth_bed" \
  "$upstream_hard" "$upstream_hard.tbi" \
  "$optimized_hard" "$optimized_hard.tbi" \
  "$upstream_gvcf" "$upstream_gvcf.tbi" \
  "$optimized_gvcf" "$optimized_gvcf.tbi" \
  "$upstream_derived" "$upstream_derived.tbi" \
  "$optimized_derived" "$optimized_derived.tbi" \
  "$upstream_anno" "$optimized_anno" \
  "$anno_input" "$anno_input.tbi" "$anno_bed"
do
  [[ -s "$required" ]] || {
    printf 'required comparison input is missing or empty: %s\n' "$required" >&2
    exit 2
  }
done
[[ ! -e "$publish_root" ]] || {
  printf 'refusing to overwrite control comparison: %s\n' "$publish_root" >&2
  exit 2
}

scratch_parent="/scratch/dayoa/sentieon-cli-control/${analysis_unit}/comparison/${SLURM_JOB_ID}"
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
result="${job_root}/result"
mkdir -p "$work" "$result"/{semantic,performance,rtg,provenance}
export TMPDIR="${job_root}/tmp"
mkdir -p "$TMPDIR"
export PATH="$hts_env/bin:/usr/bin:/bin"

printf 'started_utc=%s\nslurm_job_id=%s\nnode=%s\n' \
  "$(date -u +%FT%TZ)" "$SLURM_JOB_ID" "$(hostname)" \
  > "$result/provenance/job.txt"
"$rtg" version > "$result/provenance/rtg-version.txt"
"$bcftools" --version > "$result/provenance/bcftools-version.txt"

body_hash() {
  "$bcftools" view --no-version -H "$1" | sha256sum | awk '{print $1}'
}

semantic_header_hash() {
  "$bcftools" view --no-version -h "$1" |
    grep -E '^##(FILTER|INFO|FORMAT|contig|reference)=' |
    sha256sum | awk '{print $1}'
}

query_hash() {
  local input=$1
  {
    for region in chr1:1-1000000 chr10:1-1000000 chr22:1-1000000 \
      chrX:1-1000000 chrY:1-1000000 chrM:1-16569
    do
      "$tabix" "$input" "$region"
    done
  } | sha256sum | awk '{print $1}'
}

printf 'mode\tupstream_body_sha256\toptimized_body_sha256\tupstream_semantic_header_sha256\toptimized_semantic_header_sha256\tupstream_query_sha256\toptimized_query_sha256\n' \
  > "$result/semantic/matched-mode-hashes.tsv"
for comparison in \
  "native-hard|${upstream_hard}|${optimized_hard}" \
  "gvcf|${upstream_gvcf}|${optimized_gvcf}" \
  "from-gvcf-hard|${upstream_derived}|${optimized_derived}"
do
  IFS='|' read -r label upstream_input optimized_input <<< "$comparison"
  upstream_body="$(body_hash "$upstream_input")"
  optimized_body="$(body_hash "$optimized_input")"
  upstream_header="$(semantic_header_hash "$upstream_input")"
  optimized_header="$(semantic_header_hash "$optimized_input")"
  upstream_query="$(query_hash "$upstream_input")"
  optimized_query="$(query_hash "$optimized_input")"
  printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
    "$label" "$upstream_body" "$optimized_body" \
    "$upstream_header" "$optimized_header" \
    "$upstream_query" "$optimized_query" \
    >> "$result/semantic/matched-mode-hashes.tsv"
  [[ "$upstream_body" == "$optimized_body" ]]
  [[ "$upstream_header" == "$optimized_header" ]]
  [[ "$upstream_query" == "$optimized_query" ]]
done

upstream_native_body="$(body_hash "$upstream_hard")"
upstream_derived_body="$(body_hash "$upstream_derived")"
[[ "$upstream_native_body" != "$upstream_derived_body" ]] || {
  printf 'untouched upstream native hard and gVCF-derived hard bodies are identical\n' >&2
  exit 1
}
{
  printf 'upstream_native_body_sha256=%s\n' "$upstream_native_body"
  printf 'upstream_from_gvcf_body_sha256=%s\n' "$upstream_derived_body"
  printf 'construction_paths_differ=true\n'
} > "$result/semantic/upstream-mode-distinction.txt"

upstream_benchmark_output="${work}/upstream-annotated.vcf.gz"
optimized_benchmark_output="${work}/optimized-annotated.vcf.gz"
mkdir -p "$work/upstream-tmp" "$work/optimized-tmp"

export PYTHONPATH="$source_root/upstream-v1.7.0"
export SENTIEON_TMPDIR="$work/upstream-tmp"
/usr/bin/time -v -o "$result/performance/upstream.time.txt" \
  "$runtime_python" "$upstream_anno" \
  -v "$anno_input" -b "$anno_bed" -t "$threads" \
  "$upstream_benchmark_output" \
  2> "$result/performance/upstream.stderr.txt"

export PYTHONPATH="$source_root/optimized-v1.7.0"
export SENTIEON_TMPDIR="$work/optimized-tmp"
/usr/bin/time -v -o "$result/performance/optimized.time.txt" \
  "$runtime_python" "$optimized_anno" \
  -v "$anno_input" -b "$anno_bed" -t "$threads" \
  "$optimized_benchmark_output" \
  2> "$result/performance/optimized.stderr.txt"

upstream_anno_hash="$(gzip -dc "$upstream_benchmark_output" | sha256sum | awk '{print $1}')"
optimized_anno_hash="$(gzip -dc "$optimized_benchmark_output" | sha256sum | awk '{print $1}')"
[[ "$upstream_anno_hash" == "$optimized_anno_hash" ]] || {
  printf 'annotation outputs differ: %s != %s\n' \
    "$upstream_anno_hash" "$optimized_anno_hash" >&2
  exit 1
}
[[ "$(query_hash "$upstream_benchmark_output")" == \
   "$(query_hash "$optimized_benchmark_output")" ]]

python3 - \
  "$result/performance/upstream.time.txt" \
  "$result/performance/optimized.time.txt" \
  "$result/performance/summary.tsv" \
  "$upstream_anno_hash" <<'PY'
import pathlib
import re
import sys


def parse_time(path: pathlib.Path) -> dict[str, float]:
    text = path.read_text()
    fields = {}
    for label, key in (
        ("Elapsed (wall clock) time (h:mm:ss or m:ss)", "elapsed"),
        ("User time (seconds)", "user"),
        ("System time (seconds)", "system"),
        ("Maximum resident set size (kbytes)", "max_rss_kb"),
    ):
        match = re.search(rf"^\s*{re.escape(label)}:\s*(.+)$", text, re.M)
        if not match:
            raise SystemExit(f"missing {label!r} in {path}")
        value = match.group(1)
        if key == "elapsed":
            parts = [float(item) for item in value.split(":")]
            if len(parts) == 2:
                seconds = parts[0] * 60 + parts[1]
            elif len(parts) == 3:
                seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
            else:
                raise SystemExit(f"invalid elapsed time {value!r}")
            fields[key] = seconds
        else:
            fields[key] = float(value)
    return fields


upstream = parse_time(pathlib.Path(sys.argv[1]))
optimized = parse_time(pathlib.Path(sys.argv[2]))
reduction = 100.0 * (upstream["elapsed"] - optimized["elapsed"]) / upstream["elapsed"]
with pathlib.Path(sys.argv[3]).open("w") as output:
    output.write(
        "implementation\telapsed_seconds\tuser_seconds\tsystem_seconds\t"
        "max_rss_kb\tdecompressed_sha256\n"
    )
    for name, data in (("upstream", upstream), ("optimized", optimized)):
        output.write(
            f"{name}\t{data['elapsed']:.3f}\t{data['user']:.3f}\t"
            f"{data['system']:.3f}\t{data['max_rss_kb']:.0f}\t{sys.argv[4]}\n"
        )
    output.write(f"wall_time_reduction_percent\t{reduction:.3f}\n")
if reduction < 90.0:
    raise SystemExit(f"annotation wall-time reduction is only {reduction:.3f}%")
PY

declare -A rtg_inputs=(
  [upstream-native]="$upstream_hard"
  [upstream-from-gvcf]="$upstream_derived"
  [optimized-native]="$optimized_hard"
  [optimized-from-gvcf]="$optimized_derived"
)
for lane in upstream-native upstream-from-gvcf optimized-native optimized-from-gvcf
do
  lane_output="${work}/rtg-${lane}"
  RTG_MEM=150G "$rtg" vcfeval \
    --decompose \
    --squash-ploidy \
    --ref-overlap \
    -e "$truth_bed" \
    -b "$truth" \
    -c "${rtg_inputs[$lane]}" \
    -o "$lane_output" \
    -t "$reference_sdf" \
    --threads 16
  cp -a "$lane_output" "$result/rtg/$lane"
done

for pair in \
  "native|upstream-native|optimized-native" \
  "from-gvcf|upstream-from-gvcf|optimized-from-gvcf"
do
  IFS='|' read -r label upstream_lane optimized_lane <<< "$pair"
  upstream_summary="$result/rtg/$upstream_lane/summary.txt"
  optimized_summary="$result/rtg/$optimized_lane/summary.txt"
  cmp "$upstream_summary" "$optimized_summary"
  for category in tp tp-baseline fp fn; do
    upstream_category="$result/rtg/$upstream_lane/${category}.vcf.gz"
    optimized_category="$result/rtg/$optimized_lane/${category}.vcf.gz"
    [[ "$(body_hash "$upstream_category")" == \
       "$(body_hash "$optimized_category")" ]]
  done
  printf '%s\tidentical\n' "$label" \
    >> "$result/rtg/matched-mode-equivalence.tsv"
done

if cmp -s \
  "$result/rtg/upstream-native/summary.txt" \
  "$result/rtg/upstream-from-gvcf/summary.txt"
then
  printf 'untouched upstream RTG summaries unexpectedly match across modes\n' >&2
  exit 1
fi
diff -u \
  "$result/rtg/upstream-from-gvcf/summary.txt" \
  "$result/rtg/upstream-native/summary.txt" \
  > "$result/rtg/upstream-mode-summary.diff" || true

printf 'finished_utc=%s\n' "$(date -u +%FT%TZ)" \
  >> "$result/provenance/job.txt"
(
  cd "$result"
  find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
) > "$result/SHA256SUMS"

staging="${control_root}/.publish-comparison-${SLURM_JOB_ID}"
[[ ! -e "$staging" ]] || {
  printf 'comparison staging path already exists: %s\n' "$staging" >&2
  exit 2
}
mkdir "$staging"
cp -a "$result/." "$staging/"
printf 'status=SUCCESS\ncompleted_utc=%s\nslurm_job_id=%s\n' \
  "$(date -u +%FT%TZ)" "$SLURM_JOB_ID" \
  > "$staging/completion.receipt"
mv "$staging" "$publish_root"
printf 'published=%s\ncompleted_utc=%s\n' \
  "$publish_root" "$(date -u +%FT%TZ)"
success=1
