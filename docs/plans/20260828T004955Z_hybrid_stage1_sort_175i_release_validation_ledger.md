# Sentieon CLI 1.7.5i Hybrid Stage-1 sort and release-validation ledger

## Objective

Replace the index-only Hybrid Stage-1 repair in fork `1.7.4i` with the
vendor's documented `202503.04` behavior: stream the unsorted
`HybridStage1 --hap_bam` output through `sentieon util sort`, make HybridStage2
depend on the completed sorted BAM, release immutable fork `1.7.5i`, pin it in
a new DayOA patch, and validate two fresh HG002 slim-data 5x Illumina by 5x ONT
Bjuice plus Inflection capsules.

Controlling DayOA ledger:
`docs/plans/20260827T053503Z_dayoa_16_0_12_hiomr2_integration_release_ledger.md`

## Gate 0 inventory freeze

- Fork repo:
  `/Users/jmajor/projects/lsmc/.codex-worktrees/sentieon-cli-1-7-3i/sentieon-cli`
- Fork baseline: clean annotated `1.7.4i`, peeling to
  `829e1c5b1e100bac20fcb7fb096521d5cacda1fd`.
- Candidate branch: `codex/hybrid-stage1-sort-1.7.5i`.
- Official stable upstream: `v1.7.0` / `main`, commit
  `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`.
- Official development upstream: commit
  `dfb7f528c8c2abcf1d1f257af09972fb40c3314b`, package version `2.0.0`.
- Authoritative upstream behavior: commit
  `feabf07f210ee1838107d2add3dbcbcb0084910b`, "Sort the HybridStage1
  hap_bam output explicitly".
- `1.7.5i` was absent from the remote at inventory time. The published
  `1.7.4i` tag will not be moved.
- DayOA baseline: clean annotated `16.0.19`, peeling to
  `d25a480939340408aff732db09bb42636ea76c61`.
- The ordinary DayOA and DYEC operator checkouts contain user-owned changes;
  they are out of scope and will not be reset, cleaned, or overwritten.
- The already-running `1.7.4i` capsule is diagnostic only. Its output cannot
  satisfy release acceptance and will not be exported as this release proof.

## Execution ledger

| ID | Area | Requirement | Status | Category | Gate | Evidence | Root cause / terminal note |
|---|---|---|---|---|---|---|---|
| `BASE-001` | Fork | Freeze exact released and upstream baselines. | `SUCCESS` | plan_amendment | Gate 0 | Exact refs and clean states above; live remote refs inspected. | No newer stable upstream exists; the needed correction is on unreleased `dev`. |
| `OP-AUDIT-001` | DayOA operator tree | Inspect user-owned committed and uncommitted work and adopt relevant novel behavior. | `SUCCESS` | plan_amendment | Gate 0 | The only relevant uncommitted behavior preserves the complete native TIDDIT result directory and ploidy table. Released `16.0.19` already contains the equivalent `HIOMR2_TIDDIT_FILES` directory output, `ploidies.tab` validation/publication, package coverage, and tests. | No extra port is needed; copying the older operator-tree diff would duplicate released behavior. |
| `OP-AUDIT-002` | DYEC operator tree | Inspect user-owned commits and uncommitted work and adopt relevant novel behavior. | `SUCCESS` | plan_amendment | Gate 0 | `19.0.34..HEAD` changes only retained campaign ledgers/artifacts; the current uncommitted changes are campaign/Ganon documentation and build assets. | No release code change applies. Ganon remains disabled for these requested runs, per user direction. |
| `CLI-001` | Fork | Port upstream `feabf07` sorted haplotype BAM behavior without importing the full 2.0.0 executor/logging/pangenome line. | `SUCCESS` | feature_implementation | Gate 1 | `hybrid_stage1_hap` streams `HybridStage1 --hap_bam -` into `sentieon util sort`; the former index-only job is absent. `compileall`, AST parse, and `git diff --check` returned zero. | Narrow behavior port only; the 2.0.0 executor/logging/pangenome line remains out of scope. |
| `CLI-002` | Fork | Preserve dependency ordering: FIFO creation precedes both Stage-1 workers and HybridStage2 waits for both sorted haplotype and realigned BAMs. | `SUCCESS` | active_product_contract | Gate 1 | Direct DAG construction returned `HYBRID_STAGE1_DAG_OK`; `stage1-fifo` precedes both workers, hap worker requests zero scheduler threads, and HybridStage2 dependencies are exactly `first-stage` plus `first-stage-hap`. |  |
| `CLI-003` | Fork | Port upstream command/DAG tests and retain fork CNV/SV/ploidy contract tests. | `SUCCESS` | contract_test | Gate 1 | Added `tests/unit/test_dnascope_hybrid_stage1.py` with FIFO, sorted-BAM, command-shape, minimum-version, and dependency assertions. Existing component tests remain unchanged. | Checked-in tests express the contract; requested fresh workflow execution remains the release proof. |
| `CLI-004` | Fork | Require Sentieon driver `202503.04` for the new unsorted-stdout contract. | `SUCCESS` | config_or_startup_contract | Gate 1 | `CALLING_MIN_VERSIONS["sentieon driver"]` is `202503.04`; direct inspection assertion passed. |  |
| `BUNDLE-001` | Sentieon models | Compare the official model registry with every active Bjuice plus Inflection Hybrid and SegDup model path, then verify live bytes and required members. | `SUCCESS` | config_or_startup_contract | Gate 1 | Sentieon model registry `main` (`sentieon_models.yaml`, updated 2026-07-23) still names `HybridIlluminaONT2.0.bundle`, `SentieonIlluminaWGS2.2.bundle`, and `DNAscopeONT2.3.bundle`. Streaming SHA-256 of the three official S3 objects exactly matched live FSx: Hybrid `43cc86d...e18fcb`, Illumina `c1877fc7...d401e`, ONT `f306f61a...56f71`. `ar t` proved the Hybrid archive contains all Stage1/2/3, `hybrid.model`, `cnv.model`, `longreadsv.model`, BWA, and minimap2 members; its `bundle_info.json` identifies Hybrid 2.0, Illumina plus ONT. Active DayOA core, isolated CNV, and isolated LongReadSV rules all resolve the same Hybrid bundle; configured SegDup rules pass the exact SR and LR standalone bundles through `--sr_model` and `--lr_model`. Receipts retain commands/model provenance, and package rules consume component receipts rather than selecting models. | The `202503.03` parent directory used by the two SegDup model paths is a storage label, not stale content: both files are byte-identical to the current official registry objects. No newer Hybrid Illumina plus ONT bundle exists in the registry. |
| `CLI-005` | Fork | Commit, push, and annotate immutable `1.7.5i`. | `OPEN` | feature_implementation | Gate 2 | Pending clean release commit and remote tag verification. | Never move `1.7.4i`. |
| `DAY-001` | DayOA | Create a new immutable environment YAML pinning fork `1.7.5i`, update the explicit rule/config contract, and release the next DayOA patch from `16.0.19`. | `OPEN` | config_or_startup_contract | Gate 2 | Pending clean DayOA candidate. | Historical environment YAMLs remain unchanged. |
| `DRY-FULL-001` | HG002 full hg38 | Fresh six-manifest slim-data 5x/5x production-shaped dry command uses `-j 345 -p -T 0 -k -n`, reaches attributable `rc=0`, and submits zero jobs. | `OPEN` | contract_test | Gate 3 | Pending fresh capsule. |  |
| `DRY-CHR56-001` | HG002 chr5+chr6 | Fresh six-manifest slim-data 5x/5x chromosome-limited dry command uses `-j 345 -p -T 0 -k -n`, reaches attributable `rc=0`, and submits zero jobs. | `OPEN` | contract_test | Gate 3 | Pending fresh capsule. |  |
| `LIVE-FULL-001` | HG002 full hg38 | Continue the exact successful dry capsule live by removing only `-n`; submit Slurm jobs and reach final Bjuice plus Inflection `rc=0`. | `OPEN` | contract_test | Gate 4 | Pending dry gate. |  |
| `LIVE-CHR56-001` | HG002 chr5+chr6 | Continue the exact successful dry capsule live by removing only `-n`; submit Slurm jobs and reach final Bjuice plus Inflection `rc=0`. | `OPEN` | contract_test | Gate 4 | Pending dry gate. |  |
| `SLACK-001` | Communication | Notify John M, Mike K, and Andrew Geller only after both live controllers have submitted Slurm jobs. | `OPEN` | active_product_contract | Gate 4 | Pending both live submissions. | Dry runs intentionally submit zero jobs. |
| `SLACK-002` | Communication | Notify the same recipients only after both controllers reach attributable final `rc=0`. | `OPEN` | active_product_contract | Gate 5 | Pending both terminal successes. |  |

## Command and lifecycle contract

- Use the ordinary production Bjuice plus Inflection target shape; do not add a
  recall target or alternate DAG.
- Each dry/live pair uses one immutable analysis ID/root/checkout/manifests and
  in-clone configuration. Live differs from dry only by removing `-n`.
- Use `dy-r`, never raw Snakemake, inside the DYEC-owned or persistent
  one-pane `ubuntu` tmux controller.
- The full-genome and chromosome-5-plus-6 runs are separate fresh capsules.
- Do not patch pinned DayOA source on the headnode.
- Do not cancel, requeue, reprioritize, or otherwise intervene in Slurm.
- No export, S3 publication, FSx cleanup, or teardown is authorized by this
  ledger.

## Final report

All rows terminal: `no`

Objective complete: `no`
