# Sentieon Hybrid Model Checkpoint And Contig Finalization 1.7.2i Ledger

Date: 2026-08-10

## Objective

Release Sentieon CLI `1.7.2i` only after the deployed `1.7.1i` Hybrid path is
split at the post-`DNAModelApply` boundary, whole-contig finalization and
reference-order gather are implemented, and a matched HG002 chromosome 19-20
proof establishes output equivalence.

Linked DayOA ledger:
`/Users/jmajor/projects/lsmc/daylily-omics-analysis-hiomr2-cli172i/docs/plans/20260810T111553Z_hiomr2_cli172i_checkpoint_finalize_integration_ledger.md`

## Gate 0: Inventory Freeze

- Repository: `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-checkpoint-1.7.2i`
- Branch: `codex/hybrid-model-checkpoint-contig-finalize-1.7.2i`
- Branch base: fork `main` at `2ee45fa7995b9fcba7a7f76aff32eb766f907a46`
- Deployed tag: annotated `1.7.1i`, peeling to
  `e4f0ff8bf4ddd882cb154774178d2b40babba056`
- Runtime-tree comparison: `git diff --quiet 1.7.1i..2ee45fa -- sentieon_cli tests pyproject.toml poetry.lock` returned zero. The only base delta is the prior release-ledger closeout.
- Remote collision check: `refs/tags/1.7.2i` is absent.
- Initial repository state: clean feature branch.
- Deployed executable inventory (read-only DYEC headnode probe): Sentieon CLI
  `1.7.1+i`, Sentieon `202503.03`, and bcftools/htslib `1.23.1`. The exact
  deployed conda contract is
  `ce665216e6cf27f7dd1729335b653c5b_`.
- Reproducible local htslib audit environment:
  `/tmp/sentieon-hts-qa.r9zRPM/env`, with bcftools/htslib `1.23.1`, matching
  the deployed versions. Direct help proves `--threads` is supported by
  `bcftools view`, `norm`, `concat`, and `index`; `view`, `norm`, and `concat`
  also support `--no-version`. `index` supports `--tbi` and `--force`.
- Historical baseline: package `1.7.1+i`; Hybrid `subset-calls` and
  `concat-calls` advertise zero scheduler threads; final normalization is the
  streaming `bcftools view -a | bcftools norm -f | sentieon util vcfconvert`
  chain.
- Live-system limit: no current controller, Slurm job, or analysis root is to
  be changed by CLI implementation work. Live proof is confined to the two
  linked chr19-20 analysis roots after explicit DayOA locking.

## Acceptance Gates

1. Gate 1 - additive CLI boundary and command implementation.
2. Gate 2 - unit, formatting, typing, build, and installed-package validation.
3. Gate 3 - exact matched chr19-20 post-model and terminal-product comparison.
4. Gate 4 - clean PR merge, annotated `1.7.2i` tag, and remote verification.

## Control Ledger

| ID | Area | Requirement | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| BASE-001 | Source | Freeze exact fork/tag/base and prove runtime-tree equality | SUCCESS | contract_test | Gate 0 | orchestrator | SHAs and diff command recorded above |  | Exact deployed code lineage is frozen |
| BASE-002 | Runtime | Capture direct help/version evidence for bcftools view/norm/concat/index and Sentieon vcfconvert | IN_PROGRESS | contract_test | Gate 0 | orchestrator | Exact deployed versions and direct bcftools 1.23.1 help captured; deployed `vcfconvert` help remains pending because the bounded DYEC transport has not returned its terminal record |  | bcftools half of the audit is complete |
| CLI-001 | Hybrid core | Add explicit `--stop_after_model_apply` boundary without changing default behavior | SUCCESS | feature_implementation | Gate 1 | orchestrator | `DNAscopeHybridPipeline` writes the positional output at model apply and omits only `final-norm`; focused DAG test passes |  | Default is off and the skip/stop combination exits 2 |
| CLI-002 | Finalizer | Add strict whole-contig finalization command with explicit mode and four-core budget | SUCCESS | feature_implementation | Gate 1 | orchestrator | `HybridFinalizeContigPipeline`; exact-FAI and indexed-input validation; sequential view/norm/vcfconvert DAG; exact four-core guard |  | No shell-pipeline oversubscription |
| CLI-003 | Gather | Add strict FAI-order gather/index command with eight-core budget | SUCCESS | feature_implementation | Gate 1 | orchestrator | `HybridGatherPipeline`; duplicate/unknown/order/count checks; concat without deduplication; exact eight-core guard and TBI creation |  | No implicit discovery or filename ordering |
| CLI-004 | Threading | Thread supported reachable subset/concat/finalize/gather/convert calls without adding unsupported sort flags | SUCCESS | feature_implementation | Gate 1 | orchestrator | Direct bcftools 1.23.1 help plus argv tests; Hybrid transfer remains process-parallel and unchanged; repository search finds no `bcftools sort --threads` |  | Supported calls receive bounded budgets |
| CLI-005 | Compatibility | Prove ordinary `dnascope-hybrid` retains its original final-normalization DAG | SUCCESS | contract_test | Gate 2 | orchestrator | Default-DAG test retains `model-apply` and `final-norm`; stop-boundary test retains LongReadSV and CNVModelApply |  | Additive boundary only |
| QA-001 | Local QA | Pass focused and full tests, formatting, typing, build, and installed help/version checks | SUCCESS | contract_test | Gate 2 | orchestrator | `164 passed, 1 skipped`; changed-file Black, full Flake8, mypy (33 files), sdist/wheel build, wheel reinstall, version `1.7.2+i`, and all three command-help probes pass; doctest collection contains zero doctests |  | Pre-existing repository-wide Black drift outside changed files was not rewritten |
| LIVE-001 | Model checkpoint | Candidate checkpoint matches retained baseline post-`DNAModelApply` records | OPEN | contract_test | Gate 3 | orchestrator | Pending linked DayOA proof |  |  |
| LIVE-002 | Terminal parity | Final gVCF, SV, CNV, and normalized RSR evidence satisfy the matched parity contract | OPEN | contract_test | Gate 3 | orchestrator | Pending linked DayOA proof |  |  |
| PERF-001 | Runtime | Record core-release, per-contig, gather, vCPU-hour, and task-cost evidence | OPEN | contract_test | Gate 3 | orchestrator | Pending benchmark collector |  |  |
| DOC-001 | Documentation | Document the new boundary, commands, thread accounting, and failure contract | SUCCESS | feature_implementation | Gate 2 | orchestrator | README command examples and strict no-discovery/no-oversubscription behavior |  | Ledger retains the complete gate contract |
| RELEASE-001 | Release | Merge validated PR and create immutable annotated `1.7.2i` tag | OPEN | feature_implementation | Gate 4 | orchestrator | Tag must not precede live parity |  |  |

## Final Report

All rows terminal: no

Objective complete: no

The release tag is forbidden until `LIVE-001` and `LIVE-002` are `SUCCESS`.
