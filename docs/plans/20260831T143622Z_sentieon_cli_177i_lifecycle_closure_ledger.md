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
| `PORT-001` | Lifecycle | Audit the pre-existing staged tranche against the recorded upstream closure. | `IN_PROGRESS` | `feature_implementation` | 1 | Wave 1 | Blob comparison proves exact matches to the first three upstream commits for the core engine files, with explicit fork-local executor, redaction, and Hybrid stress additions; focused reconciliation pending. | Arrival state contains the first three upstream commits, not four. |
| `PORT-002` | Lifecycle | Port the remaining nine non-merge commits in recorded order with provenance. | `OPEN` | `feature_implementation` | 1 | Wave 1 | Pending. | Source audit corrected the earlier eight-commit count. |
| `PRES-001` | Hybrid | Preserve fork-only Hybrid components, population-VCF behavior, annotation, selection, transfer, Stage-1 topology, and finalizer repair. | `OPEN` | `active_product_contract` | 2 | Wave 1 | Pending focused and diff evidence. |  |
| `REG-001` | Executor | Prove a failed second process launch is recorded and the first child is terminated/reaped. | `OPEN` | `contract_test` | 2 | Wave 1 | Pending checked-in regression and focused result. |  |
| `REG-002` | Hybrid | Prove repeated split-worker FIFO/proc-sub Stage-1 topology completes and downstream waits for both products. | `OPEN` | `contract_test` | 2 | Wave 1 | Pre-existing staged test requires review and execution. |  |
| `QA-001` | Focused QA | Pass lifecycle and fork-Hybrid focused suites. | `OPEN` | `contract_test` | 3 | Wave 1 | Pending. |  |
| `QA-002` | Full QA | Pass full pytest, doctest, Black, mypy, Flake8, and compilation gates. | `OPEN` | `contract_test` | 3 | Wave 1 | Pending. |  |
| `PKG-001` | Distribution | Build sdist/wheel and validate a fresh wheel install, version, and help surfaces. | `OPEN` | `contract_test` | 4 | Wave 1 | Pending. |  |
| `LIVE-001` | Licensed input | Determine whether the exact licensed CASE1-M aligned-input matrix is presently accessible without mutation. | `OPEN` | `contract_test` | 4 | Wave 1 | Pending bounded local inventory. |  |
| `REL-001` | Local candidate | Produce clean local commits and exact diff/test evidence without tag, push, or release. | `OPEN` | `feature_implementation` | 5 | Wave 1 | Pending. |  |

## Completion rule

All local implementation and validation rows must be terminal. `LIVE-001` may
terminalize `BLOCKED` when the licensed engine, license, `/fsx` inputs, or
authorized compute are unavailable. The local candidate may be complete while
the immutable release objective remains incomplete; root reconciliation owns
all remote and release actions.
