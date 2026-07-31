#!/usr/bin/env bash
#SBATCH --cpus-per-task=16
#SBATCH --partition=i128nvme
#SBATCH --time=02:00:00
#SBATCH --comment=RnD

set -euo pipefail

analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-4xvrg7erk7knfs
stamp=20260731T090232Z
evidence_root="${analysis_root}/manual/sentieon-cli-issue-evidence/${analysis_unit}/${stamp}"
publish_root="${evidence_root}/provenance/full-coverage-commands"

raw_gvcf="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/hybrid-cli170/${analysis_unit}.sentdhiomr2.hybrid-cli170.g.vcf.gz"
derived_hard="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/five-chromosome-shards/${analysis_unit}.sentdhiomr2.vcf.gz"
native_hard="${analysis_root}/manual/s170h/1767/${analysis_unit}.native-cli170-hard.vcf.gz"
native_manifest="${analysis_root}/manual/s170h/1767/${analysis_unit}.native-cli170-hard.command-version.txt"
raw_rule_log="${analysis_root}/logs/slurm/sentdhiomr2_hybrid_cli170/sentdhiomr2_hybrid_cli170.${analysis_unit}.1.err"
cli_direct_url=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/720569eabf1f3dc6300b2b50526585ed_/lib/python3.11/site-packages/sentieon_cli-1.7.0.dist-info/direct_url.json
bcftools=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/d0b550089f59e4bd52f704890789231e_/bin/bcftools
bgzip=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/d0b550089f59e4bd52f704890789231e_/bin/bgzip
tabix=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/d0b550089f59e4bd52f704890789231e_/bin/tabix

for required in \
  "$raw_gvcf" "$raw_gvcf.tbi" \
  "$derived_hard" "$derived_hard.tbi" \
  "$native_hard" "$native_hard.tbi" \
  "$native_manifest" "$raw_rule_log" "$cli_direct_url" \
  "$bcftools" "$bgzip" "$tabix"
do
  [[ -s "$required" ]] || {
    printf 'required provenance input is missing or empty: %s\n' "$required" >&2
    exit 2
  }
done
[[ ! -e "$publish_root" ]] || {
  printf 'refusing to overwrite full-coverage command provenance: %s\n' \
    "$publish_root" >&2
  exit 2
}

scratch_root="$(mktemp -d /tmp/hg003-fullcov-command-provenance.XXXXXX)"
cleanup() {
  status=$?
  rm -rf -- "$scratch_root"
  exit "$status"
}
trap cleanup EXIT
result="${scratch_root}/result"
mkdir -p "$result"

awk '
  /^[[:space:]]*command=\($/ {capture=1}
  capture {print}
  capture && /^[[:space:]]*\)$/ {exit}
' "$raw_rule_log" > "$result/raw-gvcf-cli-command.txt"

cp "$native_manifest" "$result/native-hard-cli-command-version.txt"
cp "$cli_direct_url" "$result/sentieon-cli-direct-url.json"

"$bcftools" view --no-version -h "$raw_gvcf" |
  grep -E '^##(SentieonCommandLine|SentieonModelID|SentieonVcfID|bcftools_.*Command)' \
  > "$result/raw-gvcf-command-header.txt"
"$bcftools" view --no-version -h "$derived_hard" |
  grep -E '^##(SentieonCommandLine|SentieonModelID|SentieonVcfID|bcftools_.*Command)' \
  > "$result/gvcftyper-derived-hard-command-header.txt"

printf 'lane\tbgzip_valid\ttabix_valid\tcontig_count\tsample\n' \
  > "$result/product-validation.tsv"
for lane_spec in \
  "raw-cli-gvcf|$raw_gvcf" \
  "gvcftyper-derived-hard|$derived_hard" \
  "native-cli-hard|$native_hard"
do
  IFS='|' read -r lane input_vcf <<< "$lane_spec"
  "$bgzip" -t "$input_vcf"
  "$tabix" -l "$input_vcf" > "$result/${lane}.tabix-contigs.txt"
  sample="$("$bcftools" query -l "$input_vcf")"
  [[ "$sample" == "$analysis_unit" ]] || {
    printf 'unexpected sample for %s: %s\n' "$lane" "$sample" >&2
    exit 1
  }
  printf '%s\ttrue\ttrue\t%s\t%s\n' \
    "$lane" "$(wc -l < "$result/${lane}.tabix-contigs.txt")" "$sample" \
    >> "$result/product-validation.tsv"
done

{
  printf 'raw_gvcf=%s\n' "$raw_gvcf"
  printf 'derived_hard_vcf=%s\n' "$derived_hard"
  printf 'native_hard_vcf=%s\n' "$native_hard"
  printf 'native_hard_manifest=%s\n' "$native_manifest"
  printf 'raw_rule_log=%s\n' "$raw_rule_log"
  printf 'collected_utc=%s\n' "$(date -u +%FT%TZ)"
} > "$result/source-paths.txt"

(
  cd "$result"
  find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
) > "$result/SHA256SUMS"

staging="${evidence_root}/.publish-fullcov-provenance-$$"
mkdir "$staging"
cp -a "$result/." "$staging/"
mv "$staging" "$publish_root"
printf 'published=%s\n' "$publish_root"
