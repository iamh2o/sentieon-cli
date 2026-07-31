# HG003 Sentieon hard-vs-gVCF investigation and hybrid annotation PR ledger

## Objective

Explain and enumerate the full-coverage HG003 differences between the native
Sentieon CLI 1.7.0 Hybrid hard VCF and the hard VCF produced from the CLI gVCF
with GVCFtyper. Publish the exact evidence privately to S3 and file a
source-grounded upstream investigation issue. Separately submit the validated
`hybrid_anno.py` performance replacement as a ready-for-review upstream PR,
but only after a clean upstream-versus-optimized control proves semantic and
final RTG equivalence.

## Gate 0 baseline

- Controlling ledger:
  `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-anno-v1.7.0/docs/plans/20260731T090232Z_hg003_cli_hard_vs_gvcf_issue_and_hybrid_anno_pr_ledger.md`
- Local repository:
  `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-anno-v1.7.0`
- Upstream:
  `Sentieon/sentieon-cli`, `main` and tag `v1.7.0` both
  `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`
- Evidence branch:
  `codex/hybrid-anno-opt2-v1.7.0` at
  `c7d9fd4ebad013ebc76052578e967f28d2e065e9`, clean and synchronized with
  `iamh2o/sentieon-cli`
- Intended clean PR branch:
  `codex/hybrid-anno-performance-v1.7.0`, forked from exact upstream `main`
- Existing optimized branch diff:
  optimized script, focused tests, two LSMC evidence ledgers, and one Conda
  environment file. Only the optimized script, focused tests, and a minimal CI
  change may enter the upstream PR.
- Local focused-test probe:
  system Python collection failed because `vcflib` is absent. The prior
  isolated `sentieon-cli-1.7.0-opt2` environment reports `12 passed`; that
  result must be reproduced in the pinned environment before PR publication.
- Cluster:
  `preval-hiomr2`, profile `lsmc`, region `us-west-2`, cost center `RnD`
- Take49 analysis root:
  `/fsx/analysis_results/preval-hiomr2/take49/daylily-omics-analysis`
- Analysis unit:
  `HG003-4xvrg7erk7knfs`
- Valid live lanes:
  CLI gVCF/RTG Slurm `1769`, native CLI hard VCF Slurm `1767`, native-hard RTG
  Slurm `1770`, and the completed DayOA GVCFtyper-derived hard-VCF RTG lane.
- Excluded lane:
  Slurm `1768`, which used the wrong `hg38_m_giabHC` truth source.
- Full-coverage baseline:
  gVCF and GVCFtyper hard VCF both TP-call `3,825,826`, FP `2,576`, FN
  `6,064`, F-score `0.99887211`; native hard VCF TP-call `3,825,866`, FP
  `2,549`, FN `6,026`, F-score `0.99888060`.
- S3 evidence root:
  `s3://lsmc-dayoa-analysis-results-usw2/validation/sentieon-cli/hg003-fullcov-hard-vs-gvcf-20260731/`
- External publication:
  seven-day presigned URLs, one public upstream issue, and one ready-for-review
  upstream PR. No merge, tag, release, DayOA change, or HIOMR2 change.

## Control ledger

| ID | Area | Requirement | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| INV-001 | Local source | Freeze upstream/fork commits, branch scope, authentication, and local dirty state | SUCCESS | feature_implementation | Gate 0 | orchestrator | Gate 0 baseline; `gh auth status` authenticated as `iamh2o` |  | Exact local and GitHub source boundary recorded |
| INV-002 | Take49 | Record read/write visit, acquire the analysis-root write lock, and freeze exact valid input paths | SUCCESS | legitimate_safety_handling | Gate 0 | orchestrator | Take49 visit receipts; active write lock owned by `codex-hg003-sentieon-issue-pr-20260731`; frozen paths in Slurm 2057 input contract |  | Valid lanes 1767/1769/1770 retained; invalid 1768 explicitly excluded |
| INV-003 | Take49 | Inventory hashes, sizes, indexes, samples, commands, resources, versions, and valid RTG provenance | IN_PROGRESS | contract_test | Gate 0 | orchestrator | Slurm 2057 failed before comparison on model-path inventory; Slurm 2093 normalized the derived hard VCF, then failed on unconditional `INFO/ML_PROB` query; both direct FSx stderr logs and failed scratch retained; header-aware Slurm 2122 submitted | First defect: installed model is the bundle file itself. Second defect: derived hard VCF intentionally lacks the native-only `ML_PROB` header, so unconditional field extraction is invalid | Bundle path is exact; canonical export now emits `.` when `ML_PROB` is absent; compared VCF/RTG inputs remain unchanged |
| HDR-001 | Full coverage | Produce exact and semantic hard-VCF header comparisons without inspection-added header lines | OPEN | contract_test | Gate 1 | orchestrator | Slurm 2057 never reached header extraction |  |  |
| DIF-001 | Full coverage | Normalize/decompose both hard VCFs and publish complete bidirectional symmetric differences | OPEN | contract_test | Gate 1 | orchestrator | Slurm 2057 never reached comparison |  |  |
| DIF-002 | Full coverage | Enumerate bidirectional TP-call, TP-baseline, FP, and FN RTG category differences | OPEN | contract_test | Gate 1 | orchestrator | Slurm 2057 never reached comparison |  |  |
| DIF-003 | Full coverage | Reconcile directional differences to +40 TP-call, +38 TP-baseline, -27 FP, and -38 FN | OPEN | contract_test | Gate 1 | orchestrator | Slurm 2057 never reached comparison |  |  |
| CTRL-001 | Upstream control | Freeze identical HG003 5x FASTQ inputs, resources, commands, and two exact CLI implementations | SUCCESS | contract_test | Gate 2 | orchestrator | Clean FSx clones: upstream `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`; optimized `c7d9fd4ebad013ebc76052578e967f28d2e065e9`; common full-genome scope and 5x FASTQs frozen by runner |  | Both source trees clean before submission |
| CTRL-002 | Upstream control | Run untouched CLI 1.7.0 native-hard and gVCF-plus-GVCFtyper lanes | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | Slurm 2060 native hard; Slurm 2061 gVCF plus identical GVCFtyper conversion |  |  |
| CTRL-003 | Optimized control | Run optimized CLI native-hard and gVCF-plus-GVCFtyper lanes | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | Slurm 2062 native hard; Slurm 2063 gVCF plus identical GVCFtyper conversion |  |  |
| CTRL-004 | Comparison | Prove upstream reproduces the mode distinction and matched implementations are semantically and RTG identical | OPEN | contract_test | Gate 2 | orchestrator | Pending |  |  |
| PERF-001 | Performance | Prove at least 90% annotation wall-time reduction with full command/resource evidence | OPEN | contract_test | Gate 2 | orchestrator | Existing evidence: hard 98.0-98.3%, gVCF 94.4-94.9%; fresh control pending |  |  |
| S3-001 | Evidence export | Build checksum manifest and private evidence bundle without reads, alignments, references, credentials, or scratch trees | OPEN | legitimate_safety_handling | Gate 3 | orchestrator | Pending |  |  |
| S3-002 | Evidence export | Upload three full-coverage products/indexes and compact evidence, verify objects, and create seven-day URLs | OPEN | feature_implementation | Gate 3 | orchestrator | Pending |  |  |
| ISSUE-001 | GitHub | File the public upstream investigation issue only after difference and upstream-reproduction gates pass | OPEN | feature_implementation | Gate 4 | orchestrator | Pending |  |  |
| PR-001 | GitHub | Create clean upstream-main branch with only optimized script, focused tests, and minimal CI support | IN_PROGRESS | feature_implementation | Gate 4 | orchestrator | Clean worktree `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-anno-pr-v1.7.0`, branch `codex/hybrid-anno-performance-v1.7.0`; current diff is script, focused test, and CI tabix install only |  | No LSMC ledger, environment YAML, DayOA, or HIOMR2 file in PR worktree |
| PR-002 | GitHub | Reproduce focused tests and upstream checks in the pinned environment | SUCCESS | contract_test | Gate 4 | orchestrator | Pinned `sentieon-cli-1.7.0-opt2` environment: focused `12 passed`; full `137 passed`; doctest `137 passed`; configured Flake8 RC 0; Black check RC 0; mypy RC 0 |  | The initial raw Flake8 invocation lacked `Flake8-pyproject` and exposed pre-existing excluded files; rerun with the project-declared plugin honored the upstream configuration and passed |
| PR-003 | GitHub | Push fork branch and open ready-for-review upstream PR with issue and benchmark evidence | OPEN | feature_implementation | Gate 4 | orchestrator | Pending |  |  |
| LOCK-001 | Take49 | Release the analysis-root lock only after durable evidence and terminal ledger updates | OPEN | legitimate_safety_handling | Gate 5 | orchestrator | Pending |  |  |
| ACCEPT-001 | Acceptance | Terminalize every row and record issue, PR, commits, S3 prefix/expiry, checks, and residual risk | OPEN | contract_test | Gate 5 | orchestrator | Pending |  |  |

## Evidence contract

- All full-coverage comparisons use the two hard VCFs and RTG category files
  from the valid Take49 lanes named above.
- Raw headers are extracted with `bcftools view --no-version -h`.
- Allele comparison keys are reference-normalized, multiallelic-decomposed
  `CHROM,POS,REF,ALT` values; genotype, FILTER, QUAL, `LHC`, `ML_PROB`, and
  population annotations remain reported attributes.
- Directional set sizes must be shown in addition to net differences.
- Compressed-byte identity is not required. Record order, variants, genotypes,
  FILTER, INFO including `LHC`, samples, tabix queries, and RTG results are
  semantic acceptance requirements.
- The issue is an investigation request, not a claim of a confirmed Sentieon
  defect.
- The PR does not attempt to change native-hard versus gVCF semantics.

## Final report

All rows terminal: no

Objective complete: no

Status counts:

- SUCCESS: 4
- OPEN: 12
- IN_PROGRESS: 4
- ATTEMPTING_BUGFIX: 0
- DUPLICATE: 0
- NO_LONGER_NEEDED: 0
- FAIL: 0
- BLOCKED: 0
