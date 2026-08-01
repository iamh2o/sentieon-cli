# HG003 gVCF validation handoff

Created: 2026-08-01T11:17:27Z  
Handoff source task: `Investigate hybrid runtime options`  
Owner identity for the active analysis lock: `codex-sentieon-cli-171i-20260801`

## Purpose

Continue and close the exact HG003 5x Illumina plus 5x ONT validation of:

1. untouched upstream Sentieon CLI `v1.7.0` in native `--gvcf` mode;
2. the exact released accelerated fork tag `1.7.1i` in native `--gvcf`
   mode;
3. exact semantic comparison of those two gVCFs;
4. DayOA `13.0.116` `GVCFtyper` hardcuts from both gVCFs;
5. matched RTG `vcfeval` comparison;
6. separate comparison of each gVCF-derived hardcut against the corresponding
   directly produced native hard VCF;
7. final evidence publication to upstream PR 28.

The upstream semantic issue was already filed from complete earlier data. Do
not file a duplicate.

## Stop boundary from the previous task

The previous task stopped only its read-only shell monitoring loop. It did not
cancel, requeue, hold, reprioritize, or otherwise manipulate any Slurm job.
The live jobs and their dependency continue under Slurm.

Do not cancel stale dependency-only jobs 2600 or 2608 without a new, explicit
user approval for those exact job IDs. Do not administer Slurm, nodes,
partitions, or services.

## Authoritative local checkout

- Repository:
  `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-core-runtime-1.7.1i`
- Remote fork: `https://github.com/iamh2o/sentieon-cli.git`
- Upstream: `https://github.com/Sentieon/sentieon-cli.git`
- Branch: `codex/hg003-gvcf-hardcut-validation-1.7.1i`
- Handoff-base commit:
  `b3321736bb4c1465f6f2b7a6bef894592da2b1a4`
- The branch was clean and the same commit was present on the fork remote at
  the handoff snapshot.
- Controlling ledger:
  `docs/plans/20260801T101612Z_hg003_gvcf_hardcut_validation/20260801T101612Z_hg003_gvcf_hardcut_validation_ledger.md`
- Direct gVCF payload:
  `docs/plans/20260801T101612Z_hg003_gvcf_hardcut_validation/run_hg003_gvcf_core.sbatch`
- Dependent hardcut/comparison payload:
  `docs/plans/20260801T101612Z_hg003_gvcf_hardcut_validation/derive_compare_hg003_gvcf_hardcut.sbatch`
- Upstream issue body retained at:
  `docs/plans/20260801T101612Z_hg003_gvcf_hardcut_validation/sentieon_issue_body.md`
- Existing-evidence PR comment retained at:
  `docs/plans/20260801T101612Z_hg003_gvcf_hardcut_validation/upstream_pr_existing_gvcf_evidence_comment.md`

Read the controlling ledger and both payloads before taking action. The
payloads are fail-hard, atomically publish only complete results, and contain
the exact source, tool, reference, model, input, and output contracts.

## Headnode access and persistent shell

- Cluster: `preval-hiomr2`
- Region: `us-west-2`
- Headnode: `ip-10-0-0-138`
- Remote user: `ubuntu`
- Cost-center/Slurm comment: `RnD`
- Partition: `i128nvme`
- Analysis root:
  `/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x`
- Analysis-root write lock is still held by
  `codex-sentieon-cli-171i-20260801`.
- Lock status at handoff:
  `locked by codex-sentieon-cli-171i-20260801`.

Connect from the local DYEC checkout through the supported interactive path:

```bash
cd /Users/jmajor/projects/lsmc/daylily-ephemeral-cluster
source ./activate
dyec headnode connect --profile lsmc --region us-west-2 --cluster preval-hiomr2
```

Use an interactive `bash` login shell as `ubuntu`. Create a new, distinctly
named persistent tmux session for this continuation; do not take over or send
commands into unrelated Take91/Take71 controllers. Set the stable lock identity
before any analysis-root work:

```bash
export DAYOA_AGENT_ID=codex-sentieon-cli-171i-20260801
export DAYOA_AGENT_KIND=codex
export DAYOA_HUMAN_REQUESTOR=jmajor
export DAYOA_TMUX_SESSION=sentcli171i-hg003-gvcf-closeout-20260801
export DAYOA_LEDGER_PATH=/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x/validation-source/docs/plans/20260801T101612Z_hg003_gvcf_hardcut_validation/20260801T101612Z_hg003_gvcf_hardcut_validation_ledger.md
analysis_root=/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x
```

Before reading the analysis root in the continuation, record a read visit with
`dyec analysis visit`. Do not invoke raw Snakemake; this validation is already
running as direct CLI Slurm payloads and needs no DayOA controller launch.

## Exact source and tool provenance

| Component | Tag/ref | Exact commit/path |
|---|---|---|
| Official CLI baseline | upstream `v1.7.0` | `1bf377d3ce79fc4d8c2dc221e1f696441e38349d` |
| Accelerated release | fork annotated tag `1.7.1i` | `e4f0ff8bf4ddd882cb154774178d2b40babba056` |
| Release package version | PEP 621 | `1.7.1+i` |
| DayOA hardcut | annotated tag `13.0.116` | `7b5e8f7c8df82de2b7478bec7ceadb08430950ad` |
| Sentieon Genomics | release | `202503.03` |
| Official source worktree | detached, clean | `$analysis_root/checkouts/official170` |
| Release source worktree | detached, clean | `$analysis_root/checkouts/release171i` |
| DayOA source worktree | detached, clean | `$analysis_root/checkouts/dayoa-13.0.116` |
| Validation script worktree | detached at `a82654f` | `$analysis_root/validation-source` |

The direct runner injects the exact checkout through `PYTHONPATH`. Its
installed distribution metadata still causes `sentieon-cli --version` to say
`1.7.0`. This is expected and is not evidence that the release job used the
wrong code. The corrected payload separately proves the imported module path,
Git SHA, annotated tag, and PEP 621 source version `1.7.1+i`.

## Frozen input contract

- Analysis unit: `HG003-5X-CLI-RUNTIME`
- Short-read CRAM:
  `$analysis_root/prepared/HG003-5X-CLI-RUNTIME.sr.prepared.cram`
- Long-read CRAM:
  `$analysis_root/prepared/HG003-5X-CLI-RUNTIME.lr.aligned.cram`
- Scope:
  `$analysis_root/inputs/full-primary.bed`
- Scope SHA-256:
  `6f6179a3bc159e9527a56e665f8e5363fb8ee4af58696fbbdd043d1e0df6128d`
- Reference: GRCh38 no-alt analysis set.
- Model: `HybridIlluminaONT2.0.bundle`.
- dbSNP: `Homo_sapiens_assembly38.dbsnp138.vcf.gz`.
- Population VCF: `pop-v20g41-20251216.vcf.gz`.
- GIAB truth: HG003 small variants v4.2.1 `giabHC` VCF and BED.
- RTG SDF:
  `/fsx/references/genomic_data/organism_references/H_sapiens/hg38/rtg/Homo_sapiens_assembly38.fasta.sdf`
- Excluded: raw FASTQ preparation, QC, MultiQC, mosdepth, SV, CNV,
  scheduler pending time, and cluster administration.
- There is no external input sharding. Any batching printed by
  `hybrid_select` is an internal implementation detail of the optimized CLI.

## Live Slurm snapshot at 2026-08-01T11:17:27Z

| Job | Role | State | Elapsed | Stage/reason |
|---:|---|---|---:|---|
| 2606 | exact upstream `v1.7.0 --gvcf` | RUNNING | 00:30:21 | second `HybridStage2`, node `i128nvme-dy-price128nvme-1` |
| 2611 | exact released `1.7.1i --gvcf` | RUNNING | 00:28:23 | `HybridStage3`, node `i128nvme-dy-price128nvme-2` |
| 2612 | hardcut, semantic comparison, and RTG | PENDING | 00:00:00 | valid `afterok:2606:2611` dependency |
| 2600 | stale comparison attempt | PENDING | 00:00:00 | `DependencyNeverSatisfied`; do not cancel without approval |
| 2608 | stale comparison attempt | PENDING | 00:00:00 | `DependencyNeverSatisfied`; do not cancel without approval |

Submission placement for every real lane is exactly:

```text
sbatch --partition i128nvme --comment RnD --cpus-per-task=128 ...
```

The release lane had already passed the direct optimized selector:

```text
hybrid_select: workers=96 step_size=10000000 shards=504
hybrid_select: records=548884204 selected=2019928
```

At the matched post-Stage1 checkpoint, the release lane led the official lane
by about two minutes and then entered HybridStage3 while the official lane was
still in HybridStage2. Both logs were growing and contained no failure markers
at handoff.

## Logs and expected publications

```text
$analysis_root/logs/gvcf-validation/sentcli170-gvcf-2606.err
$analysis_root/logs/gvcf-validation/sentcli170-gvcf-2606.out
$analysis_root/logs/gvcf-validation/sentcli171i-gvcf-2611.err
$analysis_root/logs/gvcf-validation/sentcli171i-gvcf-2611.out
$analysis_root/logs/gvcf-validation/sentcli-gvcf-compare-2612.err
$analysis_root/logs/gvcf-validation/sentcli-gvcf-compare-2612.out
```

Successful direct lanes publish atomically to:

```text
$analysis_root/results/official170/gvcf/
$analysis_root/results/release171i/gvcf/
```

Each directory must contain the gVCF, `.tbi`, `time.txt`, `command.txt`,
`contigs.txt`, `samples.txt`, `run-manifest.txt`, and `completion.receipt`.

The dependent comparison publishes atomically to:

```text
$analysis_root/results/gvcf-hardcut-comparison/
```

The most important outputs are:

```text
semantic/matched-mode-hashes.tsv
semantic/hard-vcf-hashes.tsv
semantic/native-vs-derived.tsv
rtg/official-native.summary.txt
rtg/official-from-gvcf.summary.txt
rtg/release-native.summary.txt
rtg/release-from-gvcf.summary.txt
rtg/summary-equivalence.tsv
rtg/matched-derived-category-hashes.tsv
provenance/comparison-manifest.txt
SHA256SUMS
```

The comparison payload is intentionally fail-hard. It requires exact record
body, semantic-header, representative tabix-query, sample/contig-order, record
count, RTG summary, and RTG category-body equality between official and
released gVCF-derived outputs. Compression bytes and explicitly volatile
provenance lines may differ.

## Failed preflight attempts that produced no published results

- Jobs 2598 and 2599 failed before CLI execution because `BASH_SOURCE` resolved
  to the Slurm spool copy instead of the stable helper path.
- Job 2607 failed before CLI execution because an over-strict check interpreted
  source-injected installed distribution metadata `1.7.0` as the release source
  version.
- Jobs 2600 and 2608 are their stale dependency-only comparison children.
- Corrected direct jobs are 2606 and 2611. Corrected comparison job is 2612.
- Failed direct preflights did not publish result directories.

Do not use the failed jobs as performance evidence.

## Existing evidence already reused

Historical Take roots from Take11 through Take61 were searched before new
compute. Extant relevant roots included Take17, 20, 21, 25, 30, 41, 48, 49,
and 61. Take48/Take49 and the dedicated root below contained complete CLI
`1.7.0` evidence but could not prove exact released-tag `1.7.1i` parity because
the release tag did not yet exist:

```text
/fsx/analysis_results/preval-hiomr2/cli-gvcf-hardcut-vcfeval-20260730T130315Z
```

That completed HG003 5x/5x study established:

| Callset | TP call | FP | FN | Precision | Sensitivity | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Raw CLI gVCF | 3,604,748 | 17,651 | 227,142 | 0.9951 | 0.9407 | 0.9672 |
| GVCFtyper hard from that gVCF | 3,604,748 | 17,651 | 227,142 | 0.9951 | 0.9407 | 0.9672 |
| Native CLI hard | 3,603,895 | 17,202 | 227,997 | 0.9952 | 0.9405 | 0.9671 |

The raw-gVCF and GVCFtyper-hard RTG summaries were byte-identical, SHA-256
`74c800d876398824ea989cb5278e79b4c86f2f48826224fc64da6e9cbf6a28e2`.
After normalization, native hard versus GVCFtyper hard had 953,551 native-only,
5,018 derived-only, and 4,773,983 shared records; 925,199 native-only records
were `MLrejected`.

This evidence has already been published as:

- Sentieon issue 29:
  `https://github.com/Sentieon/sentieon-cli/issues/29`
- Existing-evidence comment on Sentieon PR 28:
  `https://github.com/Sentieon/sentieon-cli/pull/28#issuecomment-5151049963`
- Upstream optimization PR:
  `https://github.com/Sentieon/sentieon-cli/pull/28`
- Fork release:
  `https://github.com/iamh2o/sentieon-cli/releases/tag/1.7.1i`

Issue 29 is scoped as an investigation into why native hard mode differs from
gVCF plus GVCFtyper. It does not claim that this is a confirmed defect.

## DayOA environment state

Do not create another environment YAML merely because this continuation
passes. DayOA tag `13.0.116` already contains the immutable environment:

```text
workflow/envs/hiomr2_cli171i_iamh2o_v0.1.yaml
```

It pins:

```text
sentieon-cli @ git+https://github.com/iamh2o/sentieon-cli.git@1.7.1i
```

Active profile contracts already require `cli_version: "1.7.1i"`, and tests
pin the same URL. If parity passes, attach the exact validation evidence to this
existing contract. Never modify an existing versioned environment YAML in
place. If parity fails, report the mismatch and stop; do not silently change or
replace the pin.

## Continuation checklist

1. Read all applicable repo instructions, the controlling ledger, this
   handoff, and both submitted payloads.
2. Connect through DYEC as `ubuntu`, create a new persistent tmux session, set
   the stable agent/ledger variables above, and record an analysis-root read
   visit.
3. Verify the lock remains owned by
   `codex-sentieon-cli-171i-20260801`. Do not take it over under another ID.
4. Monitor jobs 2606, 2611, and 2612 with `squeue`, `sacct`, and their logs.
   Do not act on jobs 2600/2608 without explicit cancellation approval.
5. Let 2612 start automatically after both direct lanes succeed. Do not
   resubmit it while it is dependency-held.
6. On completion, inspect both direct `run-manifest.txt` files and all files in
   `results/gvcf-hardcut-comparison/`. Verify BGZF/index validity, exact source
   SHAs, wall seconds, record counts, semantic hashes, RTG summaries, and
   `SHA256SUMS`.
7. Calculate the direct process wall-time improvement from the two
   `wall_seconds` manifest fields. Do not include Slurm pending/startup time.
8. If every matched parity gate passes, update every open ledger row to a
   terminal state and add a final PR 28 comment with exact job IDs, SHAs,
   commands, timings, semantic hashes, and RTG metrics. Link issue 29 while
   keeping matched gVCF parity separate from native-hard construction-path
   divergence.
9. If a gate fails, record the exact mismatch and terminalize the ledger
   honestly. Do not weaken the gate, add a fallback, or promote a replacement
   environment.
10. Commit and push final durable evidence on
    `codex/hg003-gvcf-hardcut-validation-1.7.1i`.
11. Release the analysis-root lock only after results, ledger, and publication
    evidence are durable:

    ```bash
    dyec analysis lock release --analysis-root "$analysis_root"
    ```

12. Report explicitly whether all ledger rows are terminal, whether the exact
    objective passed, and whether stale jobs 2600/2608 remain pending.

## Minimal read-only status commands

```bash
date -u +%FT%TZ
squeue -j 2606,2611,2612,2600,2608 \
  -o '%.18i %.26j %.10T %.10M %.36R'
sacct -j 2606,2611,2612,2600,2608 \
  --format=JobIDRaw,JobName,State,Elapsed,ExitCode -n -P
tail -n 80 "$analysis_root/logs/gvcf-validation/sentcli170-gvcf-2606.err"
tail -n 80 "$analysis_root/logs/gvcf-validation/sentcli171i-gvcf-2611.err"
tail -n 80 "$analysis_root/logs/gvcf-validation/sentcli-gvcf-compare-2612.err"
dyec analysis lock status --analysis-root "$analysis_root"
```

These are monitoring commands only. No scheduler or resource intervention is
authorized by this handoff.
