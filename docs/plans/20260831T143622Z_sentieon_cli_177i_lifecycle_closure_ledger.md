# Sentieon CLI 1.7.7i lifecycle closure execution ledger

Created: 2026-08-31T14:36:22Z

## Objective

Starting from the immutable annotated fork tag `1.7.6i`, preserve all
fork-only Hybrid component, ploidy, transfer, annotation, and finalization
behavior; port the complete recorded twelve-commit upstream executor and
lifecycle closure; prove failed-second-launch teardown and logging; validate
the source and built distribution; and prepare a clean local release candidate
without tagging, pushing, publishing, or changing DayOA or DYEC.

## Boundaries

- Fork worktree only:
  `/Users/jmajor/projects/lsmc/.codex-worktrees/sentieon-cli-1-7-7i-hybrid-runtime`.
- Do not edit the DayOA ledger, DayOA source, DYEC source, remote refs, tags,
  releases, packages, AWS resources, Slurm, FSx, or S3.
- Missing licensed same-input assets is a live-evidence blocker, not permission
  to substitute regenerated or different inputs.
- `1.7.6i` remains immutable. Candidate package version is `1.7.7+i`; the
  potential annotated release tag is `1.7.7i`.

## Gate 0 baseline

| Item | Frozen value |
|---|---|
| Worktree | `/Users/jmajor/projects/lsmc/.codex-worktrees/sentieon-cli-1-7-7i-hybrid-runtime` |
| Branch | `codex/sentieon-cli-1-7-7i-hybrid-runtime` |
| Base | annotated `1.7.6i`, peeling to `40ba5dfafd8e425440ee169c6b3d1e830033c76e` |
| Governing instructions | `/Users/jmajor/projects/lsmc/AGENTS.md`; no closer `AGENTS.md` or `CLAUDE.md` exists |
| Arrival state | Partially prepared staged lifecycle port: 21 paths, 3,012 insertions and 394 deletions; no active cherry-pick or sequencer |
| Pre-existing candidate additions | `1.7.7+i` version, first engine-layer tranche, upstream tests, and `tests/integration/test_hybrid_stage1_executor.py` |
| Upstream closure | `8d3d68e`, `a34554f`, `faf6c9a`, `ffd4b60`, `56082bd`, `0f7930a`, `91c4d66`, `87f54b2`, `0d4150d`, `be5b184`, `fb9fa2c`, `76394ba` |
| Remote actions | Not authorized; no tag, push, PR, release, or publication |

## Control ledger

| ID | Area | Requirement | Status | Category | Gate | Owner | Evidence | Root cause / terminal note |
|---|---|---|---|---|---|---|---|---|
| `BASE-001` | Source | Verify exact immutable fork base, branch, instructions, and arrival state. | `SUCCESS` | `plan_amendment` | 0 | Wave 1 | Gate 0 baseline above; `git cat-file -t 1.7.6i` returned `tag` and peeled to `40ba5df`. | Candidate was partially staged on arrival and is preserved. |
| `PORT-001` | Lifecycle | Audit the pre-existing staged tranche against the recorded upstream closure. | `SUCCESS` | `feature_implementation` | 1 | Wave 1 | Blob comparison identified the first three commits (`8d3d68e`, `a34554f`, `faf6c9a`); focused reconciliation was `132 passed, 1 skipped`; preserved as `42597c0`. | Arrival state contained the first three upstream commits, not four. |
| `PORT-002` | Lifecycle | Port the remaining nine non-merge commits in recorded order with provenance. | `SUCCESS` | `feature_implementation` | 1 | Wave 1 | `09e223c`=`ffd4b60`; `4d68c23`=`56082bd`; `af1a278`=`0f7930a`; `b3ec463`=`91c4d66`; `9da97b2`=`87f54b2`; `9556e08`=`0d4150d`; `46fa538`=`be5b184`; `d49008a`=`fb9fa2c`; `8a84f56`=`76394ba`; each cherry-pick commit carries the full upstream SHA. | Source audit corrected the earlier eight-commit count. Hybrid conflicts were resolved by adding lifecycle task metadata to fork-owned jobs without removing their behavior. |
| `PRES-001` | Hybrid | Preserve fork-only Hybrid components, population-VCF behavior, annotation, selection, transfer, Stage-1 topology, and finalizer repair. | `SUCCESS` | `active_product_contract` | 2 | Wave 1 | Relative to `1.7.6i`, `dnascope_hybrid.py` and `hybrid_vcf.py` change only by required `task_name` metadata; Hybrid annotation/selection/transfer scripts are byte-identical. Focused Hybrid/lifecycle gate passed. | Fork-only CLI surfaces remain `dnascope-hybrid`, `dnascope-hybrid-finalize-contig`, and `dnascope-hybrid-gather`. |
| `REG-001` | Executor | Prove a failed second process launch is recorded and the first child is terminated/reaped. | `SUCCESS` | `contract_test` | 2 | Wave 1 | `test_mid_pipeline_spawn_failure_terminates_running_stages` and `test_failed_second_launch_reaps_first_stage_and_reports_partial_log`; `a61dc71` strengthens the latter to require a terminal first-child return code plus retained/named log. |  |
| `REG-002` | Hybrid | Prove repeated split-worker FIFO/proc-sub Stage-1 topology completes and downstream waits for both products. | `SUCCESS` | `contract_test` | 2 | Wave 1 | `tests/integration/test_hybrid_stage1_executor.py` runs the vendor-free split-worker topology 20 times; included in both focused and full green gates. |  |
| `QA-001` | Focused QA | Pass lifecycle and fork-Hybrid focused suites. | `SUCCESS` | `contract_test` | 3 | Wave 1 | `235 passed, 2 skipped in 5.44s`. | Skips are platform/test-declared and not failures. |
| `QA-002` | Full QA | Pass full pytest, doctest, Black, mypy, Flake8, and compilation gates. | `SUCCESS` | `contract_test` | 3 | Wave 1 | Full pytest `323 passed, 2 skipped`; doctest-modules `323 passed, 2 skipped`; Black `23 files would be left unchanged`; mypy `Success: no issues found in 24 source files`; Flake8 and compileall rc=0. A clean Python 3.11 candidate-metadata rerun also produced `323 passed, 2 skipped`. |  |
| `PKG-001` | Distribution | Build sdist/wheel and validate a fresh wheel install, version, and help surfaces. | `SUCCESS` | `contract_test` | 4 | Wave 1 | `uv build` produced `sentieon_cli-1.7.7+i.tar.gz` SHA256 `b367da9b...57e11a` and wheel SHA256 `6b4c523b...91e2c0`; fresh Python 3.11 and 3.14 wheel installs reported `1.7.7+i`; root, Hybrid, finalizer, and gather help surfaces returned rc=0. | Artifacts remain local under ignored `dist/`; nothing was published. |
| `LIVE-001` | Licensed input | Determine whether the exact licensed CASE1-M aligned-input matrix is presently accessible without mutation. | `TRANSFERRED` | `contract_test` | 4 | Root | Root's read-only headnode check confirmed the exact diagnostic root on `bjuiceval-19024` and Sentieon 202503.04 at `/fsx/reference_asset_mounts/sentieon-genomics-202503.04/bin/sentieon`. | No licensed command was run by Wave 1. Root owns the required analysis visit, license/input confirmation, and same-input execution. |
| `REL-001` | Local candidate | Produce clean local commits and exact diff/test evidence without tag, push, or release. | `SUCCESS` | `feature_implementation` | 5 | Wave 1 | Branch `codex/sentieon-cli-1-7-7i-hybrid-runtime` contains eleven local commits over annotated `1.7.6i`: one foundation commit representing three upstream commits, nine provenance cherry-picks, and one strengthened regression commit. `1.7.7i` does not exist locally. | No push, tag, PR, release, or publication was performed. |

## Completion rule

All local implementation and validation rows must be terminal. `LIVE-001` may
terminalize `BLOCKED` when the licensed engine, license, `/fsx` inputs, or
authorized compute are unavailable. The local candidate may be complete while
the immutable release objective remains incomplete; root reconciliation owns
all remote and release actions.

## Closeout

Closed locally: 2026-08-31T14:47:35Z

All Wave 1 local rows are terminal and successful. The package is a clean
local `1.7.7+i` candidate, but it is not a release: the root-owned licensed
same-input lane, reconciliation, annotated `1.7.7i` tag, push, and publication
remain outside this wave.
