# Sentieon CLI 1.7.0 Hybrid Annotation Fork and Full CLI Ledger

## Objective

Publish the validated raw-record `hybrid_anno.py` replacement on a public
branch of a public fork of `Sentieon/sentieon-cli`, then use that exact fork
commit for two CLI-only HG003 full-genome Hybrid runs:

- one native hard VCF run;
- one gVCF run.

Compare each completed product against the corresponding untouched Sentieon
CLI 1.7.0 result produced from the same HG003 5x ILMN FASTQs and 5x ONT FASTQ.

## Gate 0 Baseline

- Controlling ledger:
  `docs/plans/20260730T143057Z_sentieon_cli_170_hybrid_anno_fork_full_cli_ledger.md`
- Source checkout:
  `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-anno-v1.7.0`
- Upstream source/tag:
  `Sentieon/sentieon-cli` `v1.7.0`,
  commit `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`
- Local branch:
  `codex/hybrid-anno-raw-python-v1.7.0`
- Intended public fork:
  `iamh2o/sentieon-cli`
- Intended public branch:
  `codex/hybrid-anno-opt2-v1.7.0`
- Baseline repo state:
  modified `sentieon_cli/scripts/hybrid_anno.py`; untracked focused tests,
  Conda specification, and implementation ledger. These are all owned by this
  task.
- Existing fork state:
  `iamh2o/sentieon-cli` did not exist at Gate 0.
- Baseline validation:
  `pytest -q tests/unit/test_hybrid_anno.py` in
  `sentieon-cli-1.7.0-opt2` -> `12 passed`.
- Baseline diff validation:
  `git diff --check` -> RC 0.
- Live execution:
  `preval-hiomr2`, profile `lsmc`, region `us-west-2`, cost center `RnD`.
- New analysis root:
  `/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-anno-fork-v170`
- Frozen workload:
  HG003 5x ILMN paired FASTQs and 5x ONT FASTQ, hg38 contigs
  `chr1-22,X,Y,M`, 128 requested threads, NVMe-backed Slurm partition
  selection, SNV Hybrid only, no QC/SV/CNV products.
- Runtime isolation:
  every large intermediate is constructed below a unique job-specific
  `/scratch` root; declared results, logs, commands, versions, checksums, and
  compact comparison evidence are published to FSx.
- Original oracle:
  the completed untouched Sentieon CLI 1.7.0 hard VCF and gVCF products under
  the existing `cli-comparison` analysis root.
- No upstream pull request is in scope.

## Control Ledger

| ID | Area | Requirement | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| INV-001 | Source | Freeze exact upstream tag, local diff, fork destination, runtime inputs, and original oracle | SUCCESS | feature_implementation | Gate 0 | orchestrator | Gate 0 baseline above |  | Inventory frozen before external writes |
| FORK-001 | GitHub | Create public `iamh2o/sentieon-cli` fork of public upstream | OPEN | feature_implementation | Gate 1 | orchestrator | Pending |  |  |
| FORK-002 | GitHub | Commit replacement, tests, environment, and ledgers on public branch `codex/hybrid-anno-opt2-v1.7.0` | OPEN | feature_implementation | Gate 1 | orchestrator | Pending |  |  |
| TEST-001 | Local | Prove focused replacement correctness and unchanged caller interface | SUCCESS | contract_test | Gate 1 | orchestrator | `12 passed`; `command_strings.py` unchanged |  | Focused local contract is green |
| RUN-001 | Cluster | Acquire and retain the new analysis-root write lock for the two direct CLI jobs | OPEN | legitimate_safety_handling | Gate 2 | orchestrator | Pending |  |  |
| RUN-002 | Cluster | Run hard-VCF mode from the exact public fork commit on HG003 5x/5x full genome | OPEN | feature_implementation | Gate 2 | orchestrator | Pending |  |  |
| RUN-003 | Cluster | Run gVCF mode from the exact public fork commit on HG003 5x/5x full genome | OPEN | feature_implementation | Gate 2 | orchestrator | Pending |  |  |
| CMP-001 | Comparison | Validate and compare fork hard VCF with untouched 1.7.0 hard VCF | OPEN | contract_test | Gate 3 | orchestrator | Pending |  |  |
| CMP-002 | Comparison | Validate and compare fork gVCF with untouched 1.7.0 gVCF | OPEN | contract_test | Gate 3 | orchestrator | Pending |  |  |
| PROV-001 | Provenance | Prove both runs used the public fork commit and replacement script checksum | OPEN | contract_test | Gate 3 | orchestrator | Pending |  |  |
| STOP-001 | Scope | Do not run DayOA, QC, SV, CNV, concordance, Inflection, release, or package workflows | OPEN | legitimate_safety_handling | Gate 3 | orchestrator | Pending |  |  |
| LOCK-001 | Cluster | Release the analysis-root lock after all evidence is durable | OPEN | legitimate_safety_handling | Gate 4 | orchestrator | Pending |  |  |
| ACCEPT-001 | Acceptance | Terminalize every ledger row and report fork URL, branch, commit, jobs, products, and comparison | OPEN | contract_test | Gate 5 | orchestrator | Pending |  |  |

## Acceptance Contract

Each new final product must:

- be bgzip-valid, tabix-queryable, coordinate-sorted, and contain exactly the
  expected HG003 analysis sample;
- contain exactly the configured contigs and the expected Hybrid annotations;
- have a durable command/version/fork-commit manifest and direct FSx logs;
- prove the replacement annotator ran through its distinctive runtime
  diagnostics and script checksum;
- compare against the same-mode untouched 1.7.0 oracle by header contracts,
  record count, decompressed record-body SHA-256, sample, contigs, FILTER/INFO
  definitions, `LHC`, `MLrejected`, `<NON_REF>`, and bounded tabix queries.

Compressed byte identity is not required. Any semantic difference must be
quantified and attributed; it must not be hidden by normalization or fallback.
