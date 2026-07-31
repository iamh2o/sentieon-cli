#!/usr/bin/env bash
#SBATCH --job-name=sentcli-hard-diff
#SBATCH --partition=i128nvme
#SBATCH --cpus-per-task=128
#SBATCH --time=06:00:00
#SBATCH --comment=RnD

set -euo pipefail

analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-4xvrg7erk7knfs
stamp=20260731T090232Z
publish_root="${analysis_root}/manual/sentieon-cli-issue-evidence/${analysis_unit}/${stamp}"
log_root="${publish_root}/logs"
script_root="${publish_root}/scripts"

reference=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/fasta_fai_minalt/GRCh38_no_alt_analysis_set.fasta
dbsnp=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/gatk/Homo_sapiens_assembly38.dbsnp138.vcf.gz
pop_vcf=/fsx/references/genomic_data/organism_references/H_sapiens/panhg38/pop-v20g41-20251216.vcf.gz
model=/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.03/bundles/HybridIlluminaONT2.0.bundle

derived_hard="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/five-chromosome-shards/${analysis_unit}.sentdhiomr2.vcf.gz"
raw_gvcf="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/hybrid-cli170/${analysis_unit}.sentdhiomr2.hybrid-cli170.g.vcf.gz"
native_hard="${analysis_root}/manual/s170h/1767/${analysis_unit}.native-cli170-hard.vcf.gz"
derived_rtg_tar="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/concordance/_giabHC/rtg-vcfeval-scratch.tar"
raw_gvcf_rtg="${analysis_root}/manual/rtg-three-way/${analysis_unit}/cli170_gvcf_raw_hc/1769"
native_rtg="${analysis_root}/manual/rtg-three-way/${analysis_unit}/cli170_native_hard_hc/1770"
native_manifest="${analysis_root}/manual/s170h/1767/${analysis_unit}.native-cli170-hard.command-version.txt"

hts_env=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/d0b550089f59e4bd52f704890789231e_
bcftools="${hts_env}/bin/bcftools"
bgzip="${hts_env}/bin/bgzip"
tabix="${hts_env}/bin/tabix"
merge_script="${script_root}/compare_canonical_vcf_rows.py"

for path in \
  "$reference" "$dbsnp" "${dbsnp}.tbi" "$pop_vcf" "${pop_vcf}.tbi" "$model" \
  "$derived_hard" "${derived_hard}.tbi" "$raw_gvcf" "${raw_gvcf}.tbi" \
  "$native_hard" "${native_hard}.tbi" "$derived_rtg_tar" "$native_manifest" \
  "$bcftools" "$bgzip" "$tabix" "$merge_script"
do
  [[ -f "$path" ]] || { printf 'missing required input: %s\n' "$path" >&2; exit 1; }
done

mkdir -p /scratch/dayoa/sentieon-cli-evidence/"${analysis_unit}"
scratch_root=$(mktemp -d "/scratch/dayoa/sentieon-cli-evidence/${analysis_unit}/job.${SLURM_JOB_ID}.XXXXXX")
work="${scratch_root}/work"
result="${scratch_root}/result"
mkdir -p "$work" "$result"/{headers,inventory,differences,rtg,provenance}
export TMPDIR="${scratch_root}/tmp"
mkdir -p "$TMPDIR"

cleanup() {
  status=$?
  if [[ $status -eq 0 ]]; then
    rm -rf "$scratch_root"
  else
    printf 'preserved failed scratch: %s\n' "$scratch_root" >&2
  fi
}
trap cleanup EXIT

printf 'started_utc=%s\nslurm_job_id=%s\nnode=%s\n' \
  "$(date -u +%FT%TZ)" "$SLURM_JOB_ID" "$(hostname)" \
  > "$result/provenance/job.txt"
"$bcftools" --version > "$result/provenance/bcftools-version.txt"
python3 --version > "$result/provenance/python-version.txt" 2>&1
cp "$native_manifest" "$result/provenance/native-command-version.txt"
cp "$raw_gvcf_rtg/command-provenance.txt" "$result/provenance/raw-gvcf-rtg-command.txt"
cp "$native_rtg/command-provenance.txt" "$result/provenance/native-hard-rtg-command.txt"

cat > "$result/provenance/frozen-paths.txt" <<EOF
raw_cli_gvcf=${raw_gvcf}
derived_hard_vcf=${derived_hard}
native_hard_vcf=${native_hard}
derived_hard_rtg_tar=${derived_rtg_tar}
raw_cli_gvcf_rtg=${raw_gvcf_rtg}
native_hard_rtg=${native_rtg}
reference=${reference}
dbsnp=${dbsnp}
population_vcf=${pop_vcf}
hybrid_model=${model}
excluded_slurm_lane=1768
EOF

for label in derived native; do
  if [[ $label == derived ]]; then source_vcf=$derived_hard; else source_vcf=$native_hard; fi
  "$bcftools" view --no-version -h "$source_vcf" > "$result/headers/${label}.header.vcf"
  grep -E '^##(FILTER|INFO|FORMAT|contig|reference|source)' \
    "$result/headers/${label}.header.vcf" | LC_ALL=C sort \
    > "$result/headers/${label}.semantic-header.txt"
  grep -E '^##.*(Command|command|Date=)' "$result/headers/${label}.header.vcf" \
    > "$result/headers/${label}.command-header.txt" || true
  "$bcftools" query -l "$source_vcf" > "$result/inventory/${label}.samples.txt"
  "$bcftools" index -n "$source_vcf" > "$result/inventory/${label}.records.txt"
  "$bcftools" query -f '%FILTER\n' "$source_vcf" |
    awk '{count[$0]++} END {for (key in count) print key "\t" count[key]}' |
    LC_ALL=C sort > "$result/inventory/${label}.filter-counts.tsv"
  "$bcftools" query -f '[%GT\n]' "$source_vcf" |
    awk '$1=="0/0"{count++} END {print count+0}' \
    > "$result/inventory/${label}.homref-count.txt"
done
diff -u "$result/headers/derived.header.vcf" "$result/headers/native.header.vcf" \
  > "$result/headers/raw-header.diff" || true
diff -u "$result/headers/derived.semantic-header.txt" \
  "$result/headers/native.semantic-header.txt" \
  > "$result/headers/semantic-header.diff" || true
diff -u "$result/headers/derived.command-header.txt" \
  "$result/headers/native.command-header.txt" \
  > "$result/headers/command-header.diff" || true

canonicalize() {
  input_vcf=$1
  output_prefix=$2
  if "$bcftools" view --no-version -h "$input_vcf" |
    grep -q '^##INFO=<ID=ML_PROB,'
  then
    ml_prob_format='%INFO/ML_PROB'
  else
    ml_prob_format='.'
  fi
  "$bcftools" norm --threads 32 -f "$reference" -m -any -Ou "$input_vcf" |
    "$bcftools" sort -T "${work}/sort-${output_prefix}" -Oz \
      -o "${work}/${output_prefix}.norm.vcf.gz"
  "$tabix" -f -p vcf "${work}/${output_prefix}.norm.vcf.gz"
  "$bcftools" query \
    -f "%CHROM:%POS:%REF:%ALT\t%CHROM\t%POS\t%REF\t%ALT\t[%GT]\t%QUAL\t%FILTER\t%INFO/LHC\t${ml_prob_format}\t%INFO\n" \
    "${work}/${output_prefix}.norm.vcf.gz" |
    LC_ALL=C sort -T "$TMPDIR" -S 24G -t $'\t' -k1,1 \
    > "${work}/${output_prefix}.canonical.tsv"
}

canonicalize "$derived_hard" derived-hard
canonicalize "$native_hard" native-hard
python3 "$merge_script" \
  --derived "$work/derived-hard.canonical.tsv" \
  --native "$work/native-hard.canonical.tsv" \
  --output "$result/differences/full-hard-symmetric-difference.tsv.gz" \
  --summary "$result/differences/full-hard-symmetric-difference.counts.json"

mkdir -p "$work/derived-rtg"
tar -xf "$derived_rtg_tar" -C "$work/derived-rtg"
cp "$work/derived-rtg/summary.txt" "$result/rtg/derived-hard.summary.txt"
cp "$raw_gvcf_rtg/summary.txt" "$result/rtg/raw-gvcf.summary.txt"
cp "$native_rtg/summary.txt" "$result/rtg/native-hard.summary.txt"

printf 'category\tderived_records\tnative_records\tnet_native_minus_derived\n' \
  > "$result/rtg/category-record-counts.tsv"
for category in tp tp-baseline fp fn; do
  derived_input="$work/derived-rtg/${category}.vcf.gz"
  native_input="$native_rtg/${category}.vcf.gz"
  derived_count=$("$bcftools" index -n "$derived_input")
  native_count=$("$bcftools" index -n "$native_input")
  printf '%s\t%s\t%s\t%s\n' "$category" "$derived_count" "$native_count" \
    "$((native_count - derived_count))" >> "$result/rtg/category-record-counts.tsv"
  canonicalize "$derived_input" "derived-${category}"
  canonicalize "$native_input" "native-${category}"
  python3 "$merge_script" \
    --derived "$work/derived-${category}.canonical.tsv" \
    --native "$work/native-${category}.canonical.tsv" \
    --output "$result/rtg/${category}.directional-differences.tsv.gz" \
    --summary "$result/rtg/${category}.directional-differences.counts.json"
done

python3 - "$result/rtg/category-record-counts.tsv" <<'PY'
import csv
import sys

expected = {"tp": 40, "tp-baseline": 38, "fp": -27, "fn": -38}
with open(sys.argv[1], newline="") as handle:
    rows = {row["category"]: int(row["net_native_minus_derived"])
            for row in csv.DictReader(handle, delimiter="\t")}
if rows != expected:
    raise SystemExit(f"RTG net deltas do not reconcile: {rows!r} != {expected!r}")
PY

(
  cd "$analysis_root"
  sha256sum \
    "${raw_gvcf#${analysis_root}/}" "${raw_gvcf#${analysis_root}/}.tbi" \
    "${derived_hard#${analysis_root}/}" "${derived_hard#${analysis_root}/}.tbi" \
    "${native_hard#${analysis_root}/}" "${native_hard#${analysis_root}/}.tbi"
) > "$result/inventory/product-sha256.txt"
stat --printf='%n\t%s\t%y\n' \
  "$raw_gvcf" "${raw_gvcf}.tbi" "$derived_hard" "${derived_hard}.tbi" \
  "$native_hard" "${native_hard}.tbi" \
  > "$result/inventory/product-stat.tsv"
sha256sum "$reference" "$dbsnp" "$pop_vcf" "$model" \
  > "$result/inventory/resource-sha256.txt"

printf 'finished_utc=%s\n' "$(date -u +%FT%TZ)" >> "$result/provenance/job.txt"
(
  cd "$result"
  find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
) > "$result/SHA256SUMS"
tar -C "$result" -czf "$scratch_root/HG003-fullcov-sentieon-hard-vs-gvcf-evidence.tar.gz" .

mkdir -p "$publish_root"
cp -a "$result/." "$publish_root/"
cp "$scratch_root/HG003-fullcov-sentieon-hard-vs-gvcf-evidence.tar.gz" "$publish_root/"
printf 'completed_utc=%s\nslurm_job_id=%s\n' \
  "$(date -u +%FT%TZ)" "$SLURM_JOB_ID" > "$publish_root/full-coverage-evidence.receipt"
