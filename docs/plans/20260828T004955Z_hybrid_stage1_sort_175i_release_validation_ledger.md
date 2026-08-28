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
| `CLI-005` | Fork | Commit, push, and annotate immutable `1.7.5i`. | `SUCCESS` | feature_implementation | Gate 2 | Commit `d72f72c878fa03649c5a62de33e5df04c5b46a75`; pushed annotated tag `1.7.5i` peels to that commit. | `1.7.4i` was not moved. |
| `DAY-001` | DayOA | Create a new immutable environment YAML pinning fork `1.7.5i`, update the explicit rule/config contract, and release the next DayOA patch from `16.0.19`. | `SUCCESS` | config_or_startup_contract | Gate 2 | DayOA commit `22510f7cc09d362b27a5880119e16c40c0b466f9`; pushed annotated tag `16.0.20`; new immutable `hiomr2_cli175i_iamh2o_v0.7.yaml`. | Historical environment YAMLs remain unchanged. |
| `DRY-FULL-001` | HG002 full hg38 | Fresh six-manifest slim-data 5x/5x production-shaped dry command uses `-j 345 -p -T 0 -k -n`, reaches attributable `rc=0`, and submits zero jobs. | `SUCCESS` | contract_test | Gate 3 | Capsule `bjuiceval19024-hg002-5x5-full-dayoa16020-r2-20260828t010848z`; attempt `e2d4d339-ab94-4167-a55c-e819b62521e9`; controller/DayOA/Snakemake `0/0/0`; zero submissions; 118 planned jobs. |  |
| `DRY-CHR56-001` | HG002 chr5+chr6 | Fresh six-manifest slim-data 5x/5x chromosome-limited dry command uses `-j 345 -p -T 0 -k -n`, reaches attributable `rc=0`, and submits zero jobs. | `SUCCESS` | contract_test | Gate 3 | Capsule `bjuiceval19024-hg002-5x5-chr56-dayoa16020-r2-20260828t010848z`; attempt `fe1e8008-ca93-4df7-b382-f60d57d74bb0`; controller/DayOA/Snakemake `0/0/0`; zero submissions; 118 planned jobs. |  |
| `LIVE-FULL-001` | HG002 full hg38 | Continue the exact successful dry capsule live by removing only `-n`; submit Slurm jobs and reach final Bjuice plus Inflection `rc=0`. | `BLOCKED` | contract_test | Gate 4 | Attempt `9eb5a1ab-b9be-4b13-9cdb-407bb76be3c4` reached controller/DayOA/Snakemake `0/0/0`, but both packages were `COMPLETE_WITH_FAILURES`: `hybrid_small_variants` failed during finalization and hard VCF/ROH-UPD/terminal validation correctly terminalized downstream. | Release proof is scientifically incomplete despite controller success. |
| `LIVE-CHR56-001` | HG002 chr5+chr6 | Continue the exact successful dry capsule live by removing only `-n`; submit Slurm jobs and reach final Bjuice plus Inflection `rc=0`. | `BLOCKED` | contract_test | Gate 4 | Attempt `5cc8a7a2-b835-464b-a676-f8e5c8264768` reached controller/DayOA/Snakemake `0/0/0`, but both packages were `COMPLETE_WITH_FAILURES` for the same small-variant finalization defect. | Release proof is scientifically incomplete despite controller success. |
| `SLACK-001` | Communication | Notify John M, Mike K, and Andrew Geller only after both live controllers have submitted Slurm jobs. | `SUCCESS` | active_product_contract | Gate 4 | Message `1787880099.710269` in `C0ATKCY450U` after both controllers submitted. |  |
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

## 1.7.6i / DayOA 16.0.21 corrective amendment

Both `16.0.20` validation controllers reached attributable `0/0/0`, proving
that Snakemake terminalization and resilient packaging work. They do not clear
release acceptance: both packages contain four typed `FAIL` components rooted
in `hybrid_small_variants`. The exact failures were:

- full hg38: `bcftools norm` stopped at `chr1:248752466` because a valid
  hom-ref `<NON_REF>` gVCF record contained an ambiguous `N` inside REF;
- chr5+chr6: the same stage stopped at `chr6:61366327`, REF `N` versus the
  reference base `C`.

The custom split finalizer currently invokes strict-default `bcftools norm
-f`. A bounded scratch-only diagnostic ran `--check-ref s` on the two failing
regions, then re-ran `--check-ref e` on the corrected output. Both strict
verification passes succeeded. The corrections affected only reference bases
on hom-ref `<NON_REF>` records (`REF/ALT added`: two in the bounded chr1 region,
one in the bounded chr6 region).

| ID | Area | Requirement | Status | Category | Gate | Evidence | Root cause / terminal note |
|---|---|---|---|---|---|---|---|
| `REF-BASE-001` | Baseline | Preserve immutable `1.7.5i` and DayOA `16.0.20`; branch cleanly to `1.7.6i` and `16.0.21`. | `SUCCESS` | plan_amendment | Gate 0 | Fork branch `codex/hybrid-finalize-ref-repair-1.7.6i` from `1.7.5i`; DayOA branch `codex/dayoa-16-0-21-hybrid-finalize-ref-repair` from `16.0.20`; both baselines clean. | Published tags will not be moved. |
| `REF-DIAG-001` | Diagnosis | Prove the failure is a reference-mismatch policy defect, not CNV/SV/bundle failure. | `SUCCESS` | contract_test | Gate 0 | Both runs: core, CNV, LongReadSV and independent callers `PASS`; finalizer logs show exact `bcftools norm` REF mismatches; bounded `--check-ref s` plus strict `--check-ref e` verification succeeded. | Completion Slack remains withheld. |
| `REF-CLI-001` | Fork | Make contig finalization repair reference bases before normalization with explicit provenance and tests; retain strict failure for unrepaired output. | `SUCCESS` | feature_implementation | Gate 1 | Fork `1.7.6+i` adds sequential `bcftools norm --check-ref s` reference repair followed by `--check-ref e` strict verification before `vcfconvert`; checked-in DAG assertions require the four-stage dependency order and exact policies. `compileall`, a direct constructed-DAG assertion, and `git diff --check` passed; per operator direction, no pytest suite was run. | Repair is explicit in captured command provenance; mismatches that remain after repair stop at strict verification. No warning-only or record-dropping path was added. |
| `REF-DAY-001` | DayOA | Pin immutable fork `1.7.6i` in a new environment YAML and release DayOA `16.0.21`. | `OPEN` | config_or_startup_contract | Gate 2 | Pending fork release. | Do not modify `hiomr2_cli175i_iamh2o_v0.7.yaml`. |
| `REF-DRY-FULL-001` | HG002 full | Run a new clean full-hg38 dry capsule with the unchanged production target shape and required flags. | `OPEN` | contract_test | Gate 3 | Pending released pins. | A changed fork/DayOA pin requires a new capsule. |
| `REF-DRY-CHR56-001` | HG002 chr5+chr6 | Run a new clean chr5+chr6 dry capsule with the unchanged production target shape and required flags. | `OPEN` | contract_test | Gate 3 | Pending released pins. |  |
| `REF-LIVE-FULL-001` | HG002 full | Continue the exact dry capsule live and require all intended small-variant, CNV, SV, report, kitchensink, and Inflection results to validate. | `OPEN` | contract_test | Gate 4 | Pending dry success. | Controller `rc=0` alone is insufficient. |
| `REF-LIVE-CHR56-001` | HG002 chr5+chr6 | Continue the exact dry capsule live and require the same component/package validation. | `OPEN` | contract_test | Gate 4 | Pending dry success. |  |
| `REF-SLACK-001` | Communication | Send completion Slack only after both corrected capsules pass scientific/package validation. | `OPEN` | active_product_contract | Gate 5 | Completion message intentionally withheld for `16.0.20`. |  |

## Final report

All rows terminal: `no`

Objective complete: `no`
