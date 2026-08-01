#!/usr/bin/env bash
#SBATCH --cpus-per-task=128
#SBATCH --partition=i128nvme
#SBATCH --time=04:00:00
#SBATCH --comment=RnD

set -euo pipefail

analysis_root=/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis
analysis_unit=HG003-4xvrg7erk7knfs
stamp=20260731T090232Z
evidence_root="${analysis_root}/manual/sentieon-cli-issue-evidence/${analysis_unit}/${stamp}"
publish_root="${evidence_root}/postprocess"
script_root="${evidence_root}/scripts"

reference=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/fasta_fai_minalt/GRCh38_no_alt_analysis_set.fasta
derived_hard="${analysis_root}/results/day/hg38/${analysis_unit}/align/sentmm2ont/na/snv/sentdhiomr2/five-chromosome-shards/${analysis_unit}.sentdhiomr2.vcf.gz"
native_hard="${analysis_root}/manual/s170h/1767/${analysis_unit}.native-cli170-hard.vcf.gz"
hts_env=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/d0b550089f59e4bd52f704890789231e_
bcftools="${hts_env}/bin/bcftools"
tabix="${hts_env}/bin/tabix"
compare_script="${script_root}/compare_canonical_vcf_rows.py"
augment_script="${script_root}/augment_difference_tsv.py"
representation_script="${script_root}/compare_representation_maps.py"

for required in \
  "$reference" "$reference.fai" \
  "$derived_hard" "$derived_hard.tbi" \
  "$native_hard" "$native_hard.tbi" \
  "$bcftools" "$tabix" \
  "$compare_script" "$augment_script" "$representation_script" \
  "$evidence_root/full-coverage-evidence.receipt" \
  "$evidence_root/differences/full-hard-symmetric-difference.tsv.gz" \
  "$evidence_root/rtg/tp.directional-differences.tsv.gz" \
  "$evidence_root/rtg/tp-baseline.directional-differences.tsv.gz" \
  "$evidence_root/rtg/fp.directional-differences.tsv.gz" \
  "$evidence_root/rtg/fn.directional-differences.tsv.gz"
do
  [[ -s "$required" ]] || {
    printf 'required postprocess input is missing or empty: %s\n' "$required" >&2
    exit 2
  }
done
[[ ! -e "$publish_root" ]] || {
  printf 'refusing to overwrite postprocess evidence: %s\n' "$publish_root" >&2
  exit 2
}

scratch_parent="/scratch/dayoa/sentieon-cli-evidence/${analysis_unit}/postprocess/${SLURM_JOB_ID}"
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
mkdir -p "$work" "$result"/{augmented,raw,representation,summary,provenance}
export TMPDIR="${job_root}/tmp"
mkdir -p "$TMPDIR"

printf 'started_utc=%s\nslurm_job_id=%s\nnode=%s\n' \
  "$(date -u +%FT%TZ)" "$SLURM_JOB_ID" "$(hostname)" \
  > "$result/provenance/job.txt"

augment_one() {
  input=$1
  output=$2
  category=$3
  python3 "$augment_script" \
    --input "$input" \
    --output "$output" \
    --category "$category"
}

augment_one \
  "$evidence_root/differences/full-hard-symmetric-difference.tsv.gz" \
  "$result/augmented/full-hard.normalized.differences.tsv.gz" \
  full-hard-normalized
for category in tp tp-baseline fp fn; do
  augment_one \
    "$evidence_root/rtg/${category}.directional-differences.tsv.gz" \
    "$result/augmented/${category}.directional-differences.tsv.gz" \
    "$category"
done

raw_canonicalize() {
  input_vcf=$1
  output_prefix=$2
  "$bcftools" query -u \
    -f '%CHROM:%POS:%REF:%ALT\t%CHROM\t%POS\t%REF\t%ALT\t[%GT]\t%QUAL\t%FILTER\t%INFO/LHC\t%INFO/ML_PROB\t%INFO\n' \
    "$input_vcf" |
    LC_ALL=C sort -T "$TMPDIR" -S 24G -t $'\t' -k1,1 \
      > "$work/${output_prefix}.raw.canonical.tsv"
}

raw_canonicalize "$derived_hard" derived
raw_canonicalize "$native_hard" native
python3 "$compare_script" \
  --derived "$work/derived.raw.canonical.tsv" \
  --native "$work/native.raw.canonical.tsv" \
  --output "$result/raw/full-hard.raw-symmetric-difference.tsv.gz" \
  --summary "$result/raw/full-hard.raw-symmetric-difference.counts.json"
augment_one \
  "$result/raw/full-hard.raw-symmetric-difference.tsv.gz" \
  "$result/augmented/full-hard.raw.differences.tsv.gz" \
  full-hard-raw

representation_map() {
  input_vcf=$1
  output_prefix=$2
  "$bcftools" norm \
    -m -any \
    -f "$reference" \
    --old-rec-tag ORIG \
    -Ou "$input_vcf" |
    "$bcftools" query -u \
      -f '%CHROM:%POS:%REF:%ALT\t%INFO/ORIG\t%CHROM\t%POS\t%REF\t%ALT\t[%GT]\t%QUAL\t%FILTER\t%INFO\n' |
    LC_ALL=C sort -T "$TMPDIR" -S 24G -t $'\t' -k1,1 \
      > "$work/${output_prefix}.representation-map.tsv"
}

representation_map "$derived_hard" derived
representation_map "$native_hard" native
python3 "$representation_script" \
  --derived "$work/derived.representation-map.tsv" \
  --native "$work/native.representation-map.tsv" \
  --output "$result/representation/representation-equivalent-differences.tsv.gz" \
  --summary "$result/representation/representation-equivalent-differences.counts.json"

python3 - "$result/augmented" "$result/summary/classification-counts.tsv" <<'PY'
import collections
import csv
import gzip
import pathlib
import sys

source_root = pathlib.Path(sys.argv[1])
output_path = pathlib.Path(sys.argv[2])
with output_path.open("w") as output:
    output.write("file\trtg_category\tinterpretation\tcount\n")
    for path in sorted(source_root.glob("*.tsv.gz")):
        counts = collections.Counter()
        with gzip.open(path, "rt") as source:
            for row in csv.DictReader(source, delimiter="\t"):
                counts[(row["rtg_category"], row["interpretation"])] += 1
        for (category, interpretation), count in sorted(counts.items()):
            output.write(
                f"{path.name}\t{category}\t{interpretation}\t{count}\n"
            )
PY

printf 'finished_utc=%s\n' "$(date -u +%FT%TZ)" \
  >> "$result/provenance/job.txt"
(
  cd "$result"
  find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
) > "$result/SHA256SUMS"

staging="${evidence_root}/.publish-postprocess-${SLURM_JOB_ID}"
[[ ! -e "$staging" ]] || {
  printf 'postprocess staging path already exists: %s\n' "$staging" >&2
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
