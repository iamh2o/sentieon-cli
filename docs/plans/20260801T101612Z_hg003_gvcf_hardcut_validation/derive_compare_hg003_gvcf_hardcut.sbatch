#!/usr/bin/env bash
# Derive DayOA hardcuts from the two completed gVCFs, compare matched outputs,
# and run HG003 GIAB v4.2.1 RTG vcfeval for derived and native-hard paths.
# Submit only with an afterok dependency on both gVCF jobs:
#   sbatch --partition i128nvme --comment RnD --cpus-per-task=128 \
#     --dependency=afterok:<official-job>:<release-job> \
#     ./derive_compare_hg003_gvcf_hardcut.sbatch \
#     <analysis-root> <clean-dayoa-13.0.116-checkout> <release-1.7.1i-checkout>

#SBATCH --cpus-per-task=128
#SBATCH --partition=i128nvme
#SBATCH --time=08:00:00
#SBATCH --comment=RnD

set -euo pipefail

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

[[ $# -eq 3 ]] \
    || die "usage: $0 <analysis-root> <dayoa-13.0.116-checkout> <release-1.7.1i-checkout>"
analysis_root=$1
dayoa_checkout=$2
release_checkout=$3

expected_root=/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x
[[ $analysis_root == "$expected_root" ]] \
    || die "unexpected analysis root: $analysis_root"
[[ ${SLURM_JOB_ID-} =~ ^[0-9]+$ ]] || die "run this payload through sbatch"
[[ ${SLURM_CPUS_PER_TASK-} == 128 ]] \
    || die "requires --cpus-per-task=128"
[[ ${SLURM_JOB_PARTITION-} == i128nvme ]] \
    || die "requires --partition=i128nvme"

dayoa_sha=7b5e8f7c8df82de2b7478bec7ceadb08430950ad
release_sha=e4f0ff8bf4ddd882cb154774178d2b40babba056
native_release_runtime_sha=501b57d48de49ec17e91fe1675ad3714c0d4173a
original_sha=1bf377d3ce79fc4d8c2dc221e1f696441e38349d
analysis_unit=HG003-5X-CLI-RUNTIME

oracle_prefix=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/720569eabf1f3dc6300b2b50526585ed_
rtg_prefix=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/e1ff8841ae9cd380c0d64a16bcfd2861_
sentieon_root=/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.03
reference=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/fasta_fai_minalt/GRCh38_no_alt_analysis_set.fasta
reference_sdf=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/rtg/Homo_sapiens_assembly38.fasta.sdf
dbsnp=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/gatk/Homo_sapiens_assembly38.dbsnp138.vcf.gz
truth=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/controls/giab/snv/v4.2.1/HG003/giabHC/HG003.vcf.gz
truth_bed=/fsx/references/genomic_data/organism_annotations/H_sapiens/hg38/controls/giab/snv/v4.2.1/HG003/giabHC/HG003.bed

official_gvcf=$analysis_root/results/official170/gvcf/$analysis_unit.sentieon-cli.g.vcf.gz
release_gvcf=$analysis_root/results/release171i/gvcf/$analysis_unit.sentieon-cli.g.vcf.gz
official_native=$analysis_root/results/official170/hard/$analysis_unit.sentieon-cli.hard.vcf.gz
release_native=$analysis_root/results/optimized-norm-reset/hard/$analysis_unit.sentieon-cli.hard.vcf.gz
official_gvcf_manifest=$analysis_root/results/official170/gvcf/run-manifest.txt
release_gvcf_manifest=$analysis_root/results/release171i/gvcf/run-manifest.txt
official_native_manifest=$analysis_root/results/official170/hard/run-manifest.txt
release_native_manifest=$analysis_root/results/optimized-norm-reset/hard/run-manifest.txt
publish_dir=$analysis_root/results/gvcf-hardcut-comparison
dayoa_hardcut=$dayoa_checkout/workflow/scripts/hiomr2_faithful_hybrid.py

[[ ! -e $publish_dir ]] || die "publish destination already exists: $publish_dir"
for checkout_path in "$dayoa_checkout" "$release_checkout"; do
    [[ -d $checkout_path/.git || -f $checkout_path/.git ]] \
        || die "not a Git checkout: $checkout_path"
    [[ -z $(git -C "$checkout_path" status --porcelain) ]] \
        || die "checkout is dirty: $checkout_path"
done
observed_dayoa_sha=$(git -C "$dayoa_checkout" rev-parse HEAD)
[[ $observed_dayoa_sha == "$dayoa_sha" ]] \
    || die "DayOA checkout is $observed_dayoa_sha, expected $dayoa_sha"
[[ $(git -C "$dayoa_checkout" rev-parse '13.0.116^{}') == "$dayoa_sha" ]] \
    || die "DayOA tag 13.0.116 does not resolve to $dayoa_sha"
observed_release_sha=$(git -C "$release_checkout" rev-parse HEAD)
[[ $observed_release_sha == "$release_sha" ]] \
    || die "release checkout is $observed_release_sha, expected $release_sha"
[[ $(git -C "$release_checkout" rev-parse '1.7.1i^{}') == "$release_sha" ]] \
    || die "release tag 1.7.1i does not resolve to $release_sha"
[[ $(git -C "$release_checkout" cat-file -t 1.7.1i) == tag ]] \
    || die "release tag 1.7.1i is not annotated"
git -C "$release_checkout" diff --quiet \
    "$native_release_runtime_sha" "$release_sha" -- sentieon_cli \
    || die "native hard candidate and release tag differ under sentieon_cli"

for required_path in \
    "$oracle_prefix/bin/python" "$oracle_prefix/bin/bcftools" \
    "$oracle_prefix/bin/bgzip" "$oracle_prefix/bin/tabix" \
    "$rtg_prefix/bin/rtg" "$sentieon_root/bin/sentieon" \
    "$reference" "$reference.fai" "$reference_sdf" \
    "$dbsnp" "$dbsnp.tbi" "$truth" "$truth.tbi" "$truth_bed" \
    "$dayoa_hardcut" \
    "$official_gvcf" "$official_gvcf.tbi" \
    "$release_gvcf" "$release_gvcf.tbi" \
    "$official_native" "$official_native.tbi" \
    "$release_native" "$release_native.tbi" \
    "$official_gvcf_manifest" "$release_gvcf_manifest" \
    "$official_native_manifest" "$release_native_manifest"
do
    [[ -e $required_path ]] || die "required input/tool is missing: $required_path"
done
grep -Fx "source_sha=$original_sha" "$official_gvcf_manifest" >/dev/null \
    || die "official gVCF manifest has the wrong source SHA"
grep -Fx "source_sha=$release_sha" "$release_gvcf_manifest" >/dev/null \
    || die "release gVCF manifest has the wrong source SHA"
grep -Fx "source_sha=$original_sha" "$official_native_manifest" >/dev/null \
    || die "official native-hard manifest has the wrong source SHA"
grep -Fx "source_sha=$native_release_runtime_sha" "$release_native_manifest" >/dev/null \
    || die "release native-hard manifest has the wrong source SHA"

export PATH=$oracle_prefix/bin:$sentieon_root/bin:/usr/bin:/bin
export SENTIEON_INSTALL_DIR=$sentieon_root
export LD_PRELOAD=$oracle_prefix/lib/libjemalloc.so${LD_PRELOAD:+:$LD_PRELOAD}
export MALLOC_CONF=background_thread:true,metadata_thp:auto,dirty_decay_ms:5000,muzzy_decay_ms:5000
ulimit -n 65536 || die "could not raise open-file limit"

scratch_parent=/scratch/sentieon-cli-171i-hg003-5x/gvcf-hardcut-comparison/$SLURM_JOB_ID
mkdir -p "$scratch_parent"
job_root=$(mktemp -d "$scratch_parent/job.XXXXXX")
case $job_root in
    "$scratch_parent"/job.*) ;;
    *) die "unexpected scratch directory: $job_root" ;;
esac
work=$job_root/work
result=$job_root/result
mkdir -p \
    "$work/derived" "$work/rtg" \
    "$result/derived/official170" "$result/derived/release171i" \
    "$result/provenance" "$result/semantic" "$result/stats" "$result/rtg"
export TMPDIR=$job_root/tmp
export TMP=$TMPDIR
export TEMP=$TMPDIR
export SENTIEON_TMPDIR=$TMPDIR
mkdir -p "$TMPDIR"

published=0
cleanup() {
    rc=$?
    trap - EXIT INT TERM
    if (( published )); then
        rm -rf -- "$job_root"
        rmdir "$scratch_parent" 2>/dev/null || true
    else
        printf 'FAILED rc=%s; preserving NVMe evidence at %s\n' "$rc" "$job_root" >&2
    fi
    exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

official_derived=$work/derived/$analysis_unit.official170.from-gvcf.hard.vcf.gz
release_derived=$work/derived/$analysis_unit.release171i.from-gvcf.hard.vcf.gz

run_hardcut() {
    local lane=$1
    local input_gvcf=$2
    local output_vcf=$3
    local hardcut_work=$work/hardcut-$lane
    mkdir -p "$hardcut_work"
    local command=(
        env "PYTHONPATH=$dayoa_checkout"
        "$oracle_prefix/bin/python"
        "$dayoa_hardcut"
        hard-vcf
        --work-dir "$hardcut_work"
        --sentieon "$sentieon_root/bin/sentieon"
        --threads "$SLURM_CPUS_PER_TASK"
        --reference "$reference"
        --dbsnp "$dbsnp"
        --input-gvcf "$input_gvcf"
        --output-vcf "$output_vcf"
    )
    {
        printf 'lane=%s\ncommand=' "$lane"
        printf ' %q' "${command[@]}"
        printf '\n'
    } > "$result/provenance/$lane-hardcut-command.txt"
    /usr/bin/time -v -o "$result/provenance/$lane-hardcut-time.txt" \
        "${command[@]}"
    [[ -s $output_vcf && -s $output_vcf.tbi ]] \
        || die "DayOA hardcut did not produce $output_vcf and its index"
    bgzip -t "$output_vcf"
    tabix -l "$output_vcf" > "$result/semantic/$lane-hardcut-contigs.txt"
}

run_hardcut official170 "$official_gvcf" "$official_derived"
run_hardcut release171i "$release_gvcf" "$release_derived"

body_hash() {
    gzip -dc "$1" | LC_ALL=C grep -v '^#' | sha256sum | awk '{print $1}'
}

semantic_header_hash() {
    bcftools view --no-version -h "$1" 2>> "$result/provenance/bcftools-warnings.log" \
        | LC_ALL=C grep -E '^##(FILTER|INFO|FORMAT|contig|reference)=|^#CHROM' \
        | sha256sum | awk '{print $1}'
}

query_hash() {
    local input_vcf=$1
    {
        local region
        for region in \
            chr1:1-1000000 chr10:1-1000000 chr22:1-1000000 \
            chrX:1-1000000 chrY:1-1000000 chrM:1-16569
        do
            tabix "$input_vcf" "$region"
        done
    } | sha256sum | awk '{print $1}'
}

record_count() {
    bcftools index --nrecords "$1"
}

printf 'mode\tofficial_body_sha256\trelease_body_sha256\tofficial_semantic_header_sha256\trelease_semantic_header_sha256\tofficial_query_sha256\trelease_query_sha256\tofficial_records\trelease_records\n' \
    > "$result/semantic/matched-mode-hashes.tsv"
for comparison in \
    "gvcf|$official_gvcf|$release_gvcf" \
    "from-gvcf-hard|$official_derived|$release_derived"
do
    IFS='|' read -r label official_input release_input <<< "$comparison"
    official_body=$(body_hash "$official_input")
    release_body=$(body_hash "$release_input")
    official_header=$(semantic_header_hash "$official_input")
    release_header=$(semantic_header_hash "$release_input")
    official_query=$(query_hash "$official_input")
    release_query=$(query_hash "$release_input")
    official_records=$(record_count "$official_input")
    release_records=$(record_count "$release_input")
    printf '%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\n' \
        "$label" "$official_body" "$release_body" \
        "$official_header" "$release_header" \
        "$official_query" "$release_query" \
        "$official_records" "$release_records" \
        >> "$result/semantic/matched-mode-hashes.tsv"
    [[ $official_body == "$release_body" ]] \
        || die "$label record bodies differ"
    [[ $official_header == "$release_header" ]] \
        || die "$label semantic headers differ"
    [[ $official_query == "$release_query" ]] \
        || die "$label representative tabix queries differ"
    [[ $official_records == "$release_records" ]] \
        || die "$label indexed record counts differ"
done
cmp "$analysis_root/results/official170/gvcf/samples.txt" \
    "$analysis_root/results/release171i/gvcf/samples.txt"
cmp "$analysis_root/results/official170/gvcf/contigs.txt" \
    "$analysis_root/results/release171i/gvcf/contigs.txt"

declare -A hard_inputs=(
    [official-native]="$official_native"
    [official-from-gvcf]="$official_derived"
    [release-native]="$release_native"
    [release-from-gvcf]="$release_derived"
)
printf 'lane\trecord_body_sha256\tsemantic_header_sha256\trecords\n' \
    > "$result/semantic/hard-vcf-hashes.tsv"
for lane in official-native official-from-gvcf release-native release-from-gvcf; do
    input_vcf=${hard_inputs[$lane]}
    printf '%s\t%s\t%s\t%s\n' \
        "$lane" "$(body_hash "$input_vcf")" \
        "$(semantic_header_hash "$input_vcf")" \
        "$(record_count "$input_vcf")" \
        >> "$result/semantic/hard-vcf-hashes.tsv"
    bcftools stats -s - "$input_vcf" \
        > "$result/stats/$lane.bcftools-stats.txt" \
        2>> "$result/provenance/bcftools-warnings.log"
    bcftools query -f '%FILTER\n' "$input_vcf" \
        2>> "$result/provenance/bcftools-warnings.log" \
        | LC_ALL=C sort | uniq -c \
        > "$result/stats/$lane.filter-counts.txt"
done

official_native_body=$(body_hash "$official_native")
official_derived_body=$(body_hash "$official_derived")
release_native_body=$(body_hash "$release_native")
release_derived_body=$(body_hash "$release_derived")
[[ $official_native_body != "$official_derived_body" ]] \
    || die "official native hard and gVCF-derived hard record bodies unexpectedly match"
[[ $release_native_body != "$release_derived_body" ]] \
    || die "release native hard and gVCF-derived hard record bodies unexpectedly match"
{
    printf 'implementation\tnative_body_sha256\tfrom_gvcf_body_sha256\trecord_bodies_identical\n'
    printf 'official170\t%s\t%s\tfalse\n' \
        "$official_native_body" "$official_derived_body"
    printf 'release171i\t%s\t%s\tfalse\n' \
        "$release_native_body" "$release_derived_body"
} > "$result/semantic/native-vs-derived.tsv"

run_vcfeval() {
    local lane=$1
    local candidate_vcf=$2
    local lane_output=$work/rtg/$lane
    local command=(
        "$rtg_prefix/bin/rtg" vcfeval
        --decompose
        --squash-ploidy
        --ref-overlap
        -e "$truth_bed"
        -b "$truth"
        -c "$candidate_vcf"
        -o "$lane_output"
        -t "$reference_sdf"
        --threads 16
    )
    {
        printf 'lane=%s\nRTG_MEM=150G\ncommand=' "$lane"
        printf ' %q' "${command[@]}"
        printf '\n'
    } > "$result/provenance/$lane-vcfeval-command.txt"
    RTG_MEM=150G /usr/bin/time -v \
        -o "$result/provenance/$lane-vcfeval-time.txt" \
        "${command[@]}" \
        > "$result/provenance/$lane-vcfeval.stdout.txt" \
        2> "$result/provenance/$lane-vcfeval.stderr.txt"
    for expected_output in \
        summary.txt tp.vcf.gz tp-baseline.vcf.gz fp.vcf.gz fn.vcf.gz
    do
        [[ -s $lane_output/$expected_output ]] \
            || die "RTG $lane output is missing $expected_output"
    done
    cp "$lane_output/summary.txt" "$result/rtg/$lane.summary.txt"
}

for lane in official-native official-from-gvcf release-native release-from-gvcf; do
    run_vcfeval "$lane" "${hard_inputs[$lane]}"
done

cmp "$work/rtg/official-from-gvcf/summary.txt" \
    "$work/rtg/release-from-gvcf/summary.txt" \
    || die "matched gVCF-derived RTG summaries differ"
printf 'category\tofficial_from_gvcf_body_sha256\trelease_from_gvcf_body_sha256\tidentical\n' \
    > "$result/rtg/matched-derived-category-hashes.tsv"
for category in tp tp-baseline fp fn; do
    official_category=$work/rtg/official-from-gvcf/$category.vcf.gz
    release_category=$work/rtg/release-from-gvcf/$category.vcf.gz
    official_category_hash=$(body_hash "$official_category")
    release_category_hash=$(body_hash "$release_category")
    [[ $official_category_hash == "$release_category_hash" ]] \
        || die "matched gVCF-derived RTG $category record bodies differ"
    printf '%s\t%s\t%s\ttrue\n' \
        "$category" "$official_category_hash" "$release_category_hash" \
        >> "$result/rtg/matched-derived-category-hashes.tsv"
done

if cmp -s "$work/rtg/official-native/summary.txt" \
    "$work/rtg/official-from-gvcf/summary.txt"; then
    die "official native-hard and gVCF-derived RTG summaries unexpectedly match"
fi
if cmp -s "$work/rtg/release-native/summary.txt" \
    "$work/rtg/release-from-gvcf/summary.txt"; then
    die "release native-hard and gVCF-derived RTG summaries unexpectedly match"
fi
diff -u \
    "$work/rtg/official-from-gvcf/summary.txt" \
    "$work/rtg/official-native/summary.txt" \
    > "$result/rtg/official-native-vs-derived-summary.diff" || true
diff -u \
    "$work/rtg/release-from-gvcf/summary.txt" \
    "$work/rtg/release-native/summary.txt" \
    > "$result/rtg/release-native-vs-derived-summary.diff" || true
{
    printf 'comparison\tsummary_identical\n'
    printf 'official-from-gvcf-vs-release-from-gvcf\ttrue\n'
    printf 'official-native-vs-official-from-gvcf\tfalse\n'
    printf 'release-native-vs-release-from-gvcf\tfalse\n'
} > "$result/rtg/summary-equivalence.tsv"

cp "$official_derived" "$official_derived.tbi" "$result/derived/official170/"
cp "$release_derived" "$release_derived.tbi" "$result/derived/release171i/"
cp "$official_gvcf_manifest" "$result/provenance/official170-gvcf-run-manifest.txt"
cp "$release_gvcf_manifest" "$result/provenance/release171i-gvcf-run-manifest.txt"
cp "$official_native_manifest" "$result/provenance/official170-native-run-manifest.txt"
cp "$release_native_manifest" "$result/provenance/release171i-native-run-manifest.txt"
{
    printf 'status=SUCCESS\n'
    printf 'completed_utc=%s\n' "$(date -u +%FT%TZ)"
    printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
    printf 'slurm_partition=%s\n' "$SLURM_JOB_PARTITION"
    printf 'slurm_cpus_per_task=%s\n' "$SLURM_CPUS_PER_TASK"
    printf 'dayoa_tag=13.0.116\n'
    printf 'dayoa_sha=%s\n' "$dayoa_sha"
    printf 'dayoa_hardcut_script_sha256=%s\n' \
        "$(sha256sum "$dayoa_hardcut" | awk '{print $1}')"
    printf 'original_cli_sha=%s\n' "$original_sha"
    printf 'release_cli_sha=%s\n' "$release_sha"
    printf 'release_native_runtime_sha=%s\n' "$native_release_runtime_sha"
    printf 'release_native_runtime_code_matches_tag=true\n'
    printf 'rtg_version=%s\n' "$($rtg_prefix/bin/rtg version | head -1)"
    printf 'bcftools_version=%s\n' "$(bcftools --version | head -1)"
} > "$result/provenance/comparison-manifest.txt"
(
    cd "$result"
    find . -type f -print0 | LC_ALL=C sort -z | xargs -0 sha256sum
) > "$result/SHA256SUMS"

publish_parent=$(dirname "$publish_dir")
publish_basename=$(basename "$publish_dir")
mkdir -p "$publish_parent"
publish_stage=$(mktemp -d "$publish_parent/.${publish_basename}.publish.XXXXXX")
cp -a "$result/." "$publish_stage/"
mv "$publish_stage" "$publish_dir"
published=1
printf 'Published completed gVCF/hardcut comparison to %s\n' "$publish_dir"
