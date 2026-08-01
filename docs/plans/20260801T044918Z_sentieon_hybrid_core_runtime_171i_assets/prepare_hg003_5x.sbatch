#!/usr/bin/env bash
# Prepare one immutable HG003 5x SR/LR alignment pair from raw slim FASTQs.
# Submit only with:
#   sbatch --partition i128nvme --comment RnD --cpus-per-task=128 ... \
#     ./prepare_hg003_5x.sbatch <analysis-root>

set -euo pipefail

die() {
    printf 'ERROR: %s\n' "$*" >&2
    exit 2
}

[[ $# -eq 1 ]] || die "usage: $0 <analysis-root>"
analysis_root=$1
expected_root=/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x
[[ $analysis_root == "$expected_root" ]] || die "unexpected analysis root: $analysis_root"
[[ ${SLURM_JOB_ID-} =~ ^[0-9]+$ ]] || die "run this payload through sbatch"
[[ ${SLURM_CPUS_PER_TASK-} == 128 ]] || die "requires --cpus-per-task=128"
[[ ${SLURM_JOB_PARTITION-} == i128nvme ]] || die "requires --partition=i128nvme"

oracle_prefix=/fsx/resources/environments/conda/ubuntu/ip-10-0-0-138/720569eabf1f3dc6300b2b50526585ed_
sentieon_root=/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.03
reference=/fsx/references/genomic_data/organism_references/H_sapiens/hg38/fasta_fai_minalt/GRCh38_no_alt_analysis_set.fasta
model_bundle=$sentieon_root/bundles/HybridIlluminaONT2.0.bundle
sr_r1=/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/NovaSeqX_WHGS_TruSeqPF_HG002-007/downsampled/HG003_5x_R1.fastq.gz
sr_r2=/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/NovaSeqX_WHGS_TruSeqPF_HG002-007/downsampled/HG003_5x_R2.fastq.gz
lr_fastq=/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/agbt_2026/ont/HG003_5x.cleaned.primary.fastq.gz
expected_sr_r1_sha=f71e9a78961dcbea61b6e11f4c89fbc7df85300708ea1de02f176bc7ff212055
expected_sr_r2_sha=a60f04dc59a549e7f6a7d5ca78528004712fcb3f7dbdfd2bab3ddc865dbc0bb6
expected_lr_fastq_sha=93b0adac68dc4ce3c1127e3bd0a97f71abc69c55e5dd56fa00c7409d6f9c8637
analysis_unit=HG003-5X-CLI-RUNTIME
prepared_dir=$analysis_root/prepared

[[ -d $analysis_root ]] || die "analysis root does not exist: $analysis_root"
[[ ! -e $prepared_dir ]] || die "prepared output already exists: $prepared_dir"
for input_path in \
    "$reference" "$reference.fai" "$model_bundle" "$sr_r1" "$sr_r2" \
    "$lr_fastq" "$oracle_prefix/bin/igzip" "$oracle_prefix/bin/mbuffer" \
    "$oracle_prefix/bin/samtools" "$sentieon_root/bin/sentieon"
do
    [[ -e $input_path ]] || die "required input/tool is missing: $input_path"
done
sr_r1_sha=$(sha256sum "$sr_r1" | awk '{print $1}')
sr_r2_sha=$(sha256sum "$sr_r2" | awk '{print $1}')
lr_fastq_sha=$(sha256sum "$lr_fastq" | awk '{print $1}')
[[ $sr_r1_sha == "$expected_sr_r1_sha" ]] || die "Illumina R1 SHA-256 mismatch"
[[ $sr_r2_sha == "$expected_sr_r2_sha" ]] || die "Illumina R2 SHA-256 mismatch"
[[ $lr_fastq_sha == "$expected_lr_fastq_sha" ]] || die "ONT FASTQ SHA-256 mismatch"
ar t "$model_bundle" | grep -Fx bwa.model >/dev/null \
    || die "model bundle is missing bwa.model"
ar t "$model_bundle" | grep -Fx minimap2.model >/dev/null \
    || die "model bundle is missing minimap2.model"

export SENTIEON_INSTALL_DIR=$sentieon_root
export PATH=$oracle_prefix/bin:$sentieon_root/bin:$PATH
export LD_PRELOAD=$oracle_prefix/lib/libjemalloc.so${LD_PRELOAD:+:$LD_PRELOAD}
export bwt_max_mem=180G
export MALLOC_CONF=background_thread:true,metadata_thp:auto,dirty_decay_ms:5000,muzzy_decay_ms:5000
ulimit -n 65536 || die "could not raise open-file limit"

scratch_parent=/scratch/sentieon-cli-171i-hg003-5x/prepare/$SLURM_JOB_ID
mkdir -p "$scratch_parent"
job_root=$(mktemp -d "$scratch_parent/job.XXXXXX")
work=$job_root/work
tmp=$job_root/tmp
sort_tmp=$job_root/sort
mkdir -p "$work" "$tmp" "$sort_tmp"
export TMPDIR=$tmp
export TMP=$tmp
export TEMP=$tmp
export SENTIEON_TMPDIR=$tmp

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

sentieon=$sentieon_root/bin/sentieon
threads=$SLURM_CPUS_PER_TASK
sr_rg="@RG\\tID:$analysis_unit-sr\\tSM:$analysis_unit\\tLB:HG003-SR5X\\tPL:ILLUMINA"
lr_rg="@RG\\tID:$analysis_unit-lr\\tSM:$analysis_unit\\tLB:HG003-ONT5X\\tPL:ONT\\tLR:1"
sr_bam=$work/$analysis_unit.sr.aligned.bam
sr_score=$work/$analysis_unit.sr.score.txt.gz
sr_metrics=$work/$analysis_unit.sr.prepared.metrics.txt
sr_cram=$work/$analysis_unit.sr.prepared.cram
lr_cram=$work/$analysis_unit.lr.aligned.cram

start_epoch=$(date +%s)
"$sentieon" bwa mem \
    -t "$threads" -k 19 -Y -M -K 10000000 \
    -x "$model_bundle/bwa.model" -R "$sr_rg" "$reference" \
    <(igzip -cd -T 32 -q "$sr_r1") \
    <(igzip -cd -T 32 -q "$sr_r2") \
| mbuffer -m 128G -q -s 2M \
| "$sentieon" util sort \
    -t "$threads" --reference "$reference" \
    --cram_write_options version=3.0,compressor=rans \
    --sortblock_thread_count "$threads" --bam_compression 1 \
    --temp_dir "$sort_tmp" --intermediate_compress_level 1 \
    --block_size 4G --sam2bam -o "$sr_bam" -
samtools index -@ "$threads" "$sr_bam"
"$sentieon" driver \
    --reference "$reference" --thread_count "$threads" --temp_dir "$tmp" \
    --input "$sr_bam" --algo LocusCollector "$sr_score"
"$sentieon" driver \
    --reference "$reference" --thread_count "$threads" --temp_dir "$tmp" \
    --input "$sr_bam" --algo Dedup --score_info "$sr_score" \
    --metrics "$sr_metrics" \
    --cram_write_options version=3.0,compressor=rans "$sr_cram"
samtools index -@ "$threads" "$sr_cram"
samtools quickcheck -v "$sr_cram"

gzip -dc -- "$lr_fastq" \
| "$sentieon" minimap2 \
    -a -Y -t "$threads" -x "$model_bundle/minimap2.model" \
    -R "$lr_rg" "$reference" /dev/stdin \
| "$sentieon" util sort \
    -i - -t "$threads" --reference "$reference" -o "$lr_cram" --sam2bam \
    --cram_write_options version=3.0,compressor=rans
samtools index -@ "$threads" "$lr_cram"
samtools quickcheck -v "$lr_cram"
end_epoch=$(date +%s)

publish_stage=$(mktemp -d "$analysis_root/.prepared.publish.XXXXXX")
cp -p "$sr_cram" "$sr_cram.crai" "$sr_metrics" "$lr_cram" "$lr_cram.crai" \
    "$publish_stage/"
{
    printf 'analysis_unit=%s\n' "$analysis_unit"
    printf 'slurm_job_id=%s\n' "$SLURM_JOB_ID"
    printf 'slurm_partition=%s\n' "$SLURM_JOB_PARTITION"
    printf 'slurm_cpus_per_task=%s\n' "$SLURM_CPUS_PER_TASK"
    printf 'start_epoch=%s\n' "$start_epoch"
    printf 'end_epoch=%s\n' "$end_epoch"
    printf 'wall_seconds=%s\n' "$((end_epoch - start_epoch))"
    printf 'reference=%s\n' "$reference"
    printf 'model_bundle=%s\n' "$model_bundle"
    printf 'sr_r1=%s\n' "$sr_r1"
    printf 'sr_r1_sha256=%s\n' "$sr_r1_sha"
    printf 'sr_r2=%s\n' "$sr_r2"
    printf 'sr_r2_sha256=%s\n' "$sr_r2_sha"
    printf 'lr_fastq=%s\n' "$lr_fastq"
    printf 'lr_fastq_sha256=%s\n' "$lr_fastq_sha"
    printf 'sr_read_group=%s\n' "$sr_rg"
    printf 'lr_read_group=%s\n' "$lr_rg"
    sha256sum "$sr_cram" "$lr_cram"
} > "$publish_stage/preparation-manifest.txt"
mv "$publish_stage" "$prepared_dir"
published=1
printf 'Published frozen HG003 preparations to %s\n' "$prepared_dir"
