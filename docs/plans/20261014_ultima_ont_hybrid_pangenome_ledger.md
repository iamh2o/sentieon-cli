# Ultima + ONT hybrid-pangenome CLI — implementation ledger

## Current continuation state

Updated: 2026-10-14. Objective: refresh `iamh2o/sentieon-cli` from upstream
`v2.0.0` and implement experimental aligned Ultima+ONT hybrid-pangenome calling
using released models. Stop condition: committed source and documentation,
explicit provenance and validation evidence or blockers, every row terminal.
Scientific suitability and production acceptance require separate evidence.

Working repository: `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-checkpoint-1.7.2i`.
Branch: `codex/ultima-ont-hybrid-pangenome-20261014`, created from clean fork
`1.7.7i` (`c219fc1d4c4253e8a05f0c4aeb28b7605c6e5094`). Upstream fetched:
`v2.0.0` (`a0016609f411f1656bd29617a2344a0a97fe5ea9`).

Authority: user explicitly requested “PLEASE IMPLEMENT THIS PLAN,” including
the fork refresh and experimental reuse of the ILMN+ONT joint model. Local
source/docs/ledger edits and commits are authorized. Tests require two explicit
approvals under the user policy; none are recorded for this execution. Live
evaluation also lacks named inputs and compute scope. No release, push, PR,
branch merge, deployment, DayOA/DYEC adoption, or container build is authorized
by this implementation. Vendor bundles and existing tags remain immutable.

Completed: baseline frozen and upstream source delta integrated with fork
features preserved. Refresh commit is the commit containing this ledger state.
No tests, runtime evaluation, publication, release, or deployment performed.
Next action: add the experimental Ultima mode to the upstream HybridPangenome
class, with strict asset/input validation and provenance lifecycle.

## Gate 0 inventory and evidence

- Origin: `https://github.com/iamh2o/sentieon-cli.git`.
- Starting local branch was clean `main`, HEAD `025b49fd16f088dc2c0e08daeb75ea7463ebf7e2`.
- Explicitly fetched fork `1.7.7i` and upstream `v2.0.0` without other tags.
- `git status --short --branch` after branch creation: only
  `## codex/ultima-ont-hybrid-pangenome-20261014` (clean).
- `git merge-base HEAD v2.0.0`: `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`.
- `git diff <common-base> HEAD --stat`: fork changes in 80 files.
- `git diff <common-base> v2.0.0 --name-status`: upstream delta includes new
  HybridPangenome, shared stages, graph metadata, and lifecycle changes.
- A direct replacement with upstream would delete fork-only commands/scripts,
  tests, and historical ledgers. Integrate the delta and port conflicting fork
  behavior into the new shared stages instead.
- Only sample Git hooks are installed; `core.hooksPath` is unset.
- No baseline tests run: explicitly gated. No installed driver/runtime model
  availability is asserted from source inspection.
- DayOA/DYEC are outside scope; their unrelated dirty work is untouched.

## Implementation contract

Extend `hybrid-pangenome` with `--experimental_ultima` and required-in-mode
`--sr_model_bundle PATH`; `-m` remains the joint hybrid-pangenome bundle.
Accept aligned duplicate-marked Ultima and aligned ONT BAM/CRAM only, through
`--sr_aln` / `--lr_aln`, with one shared sample, unique valid read groups,
matching reference dictionaries, explicit GBZ/HAPL/population/reference files.
Reject unsupported input/caller modes. Preserve the original short-read,
ONT, and lifted short-read channels (`LR:0`, `LR:1`, `LR:2` respectively).
Scope UltimaReadFilter to Ultima read groups and preserve Ultima auxiliary tags.

Reuse upstream joint k-mers → personalized graph → ONT graph updates and
LongReadSV → Ultima realignment/liftover → joint small variants/PangenomeSV.
Outputs: indexed small-variant/SV VCFs, ploidy JSON, indexed lifted alignment,
native logs/metrics, and an experimental provenance receipt. Failures and
interruptions must never claim completion. Additional callers and new gVCF
behavior are outside this initial implementation.

| Role | Selected asset |
|---|---|
| Driver | Sentieon 202503.04 or later; verify at execution |
| Joint small variants/model application | `HybridPangenomeIlluminaONT1.0.bundle/dnascope.model`, experimental for Ultima |
| Graph read extraction | Joint bundle `extract.model` |
| Ultima graph alignment/liftover | `SentieonUltimaPangenomeRealignWGS1.3.bundle/minimap2.model` |
| ONT SV | Joint bundle `longreadsv.model` |
| Graph/haplotypes | Matching HPRC v2.1 GRCh38 GBZ/HAPL |
| Population | `SentieonVcfID=population-hprc-v2.0-20260528` |

Do not rewrite vendor metadata, repack bundles, bypass reference/population
checks, silently substitute models, or infer accuracy from completion.

## Control ledger

All rows belong to `iamh2o/sentieon-cli`. Gates: G0 baseline, G1 refresh,
G2 implementation, G3 focused tests, G4 scientific evaluation, G5 closeout.

| ID | Requirement | Status | Category | Gate | Owner | Evidence / acceptance | Root cause / terminal note |
|---|---|---|---|---|---|---|---|
| UOP-001 | Freeze fork, upstream, and model baseline | SUCCESS | config_or_startup_contract | G0 | Implementer | Gate 0 above; model evidence below | Research and fresh Git identities recorded; runtime assets not locally verified |
| UOP-002 | Refresh fork to upstream 2.0.0 preserving fork features | SUCCESS | feature_implementation | G1 | Implementer | Refresh review below; retained public-command inventory | Source integration complete; executable regression evidence gated in UOP-006 |
| UOP-003 | Model-role selection and asset validation | OPEN | config_or_startup_contract | G2 | Implementer | Member routing, immutable bundles, graph/population identities | — |
| UOP-004 | Aligned Ultima+ONT hybrid-pangenome stages | OPEN | feature_implementation | G2 | Implementer | Joint DAG, scoped filtering, three read-group channels | — |
| UOP-005 | Outputs, errors, logs, experimental provenance | OPEN | feature_implementation | G2 | Implementer | Output/index contract and failure-aware receipt | — |
| UOP-006 | Focused CLI and fork regression checks | BLOCKED | contract_test | G3 | Implementer | Prepare cases and commands; execution pending | User policy requires two explicit test approvals; not granted |
| UOP-007 | Bounded matched-input scientific evaluation | BLOCKED | contract_test | G4 | Operator | Paired inputs, truth, reference set, compute scope, metrics | Named assets and approved execution scope absent |
| UOP-008 | Document, commit, close out implementation | OPEN | feature_implementation | G5 | Implementer | Usage, model matrix, limitations, commits, terminal counts | Publication/release separate |

## Model research evidence

Prior planning inspected public bundle metadata and small members with bounded
HTTP Range reads; no full bundle download or driver execution. Registry:
<https://github.com/Sentieon/sentieon-models/blob/main/sentieon_models.yaml>.
Release: <https://github.com/Sentieon/sentieon-cli/releases/tag/v2.0.0>.
Public bundle prefix: `https://s3.amazonaws.com/sentieon-release/other/`.

| Bundle | Bytes | Metadata |
|---|---:|---|
| `HybridUltimaONT1.1.bundle` | 63491156 | DNAscope Hybrid; Ultima/ONT; minScriptVersion 1.2.1; internal bundleVersion 1.0 |
| `SentieonUltimaPangenomeRealignWGS1.3.bundle` | 919927022 | Sentieon pangenome; Ultima; minScriptVersion 1.5.0; bundleVersion 1.3; graph hprc-v2.0-mc-grch38.gbz; population-hprc-v2.0+gnomad-v4.1.0-20251216 |
| `HybridPangenomeIlluminaONT1.0.bundle` | 511706146 | Hybrid pangenome; Illumina/ONT; minScriptVersion 2.0.0; bundleVersion 1.0; graph hprc-v2.1-mc-grch38.gbz; population-hprc-v2.0-20260528 |

Measured SHA256 of selected small members:

- Both hybrid bundles' `longreadsv.model`:
  `2467ce218f6b9e9bd65f454fb08ba8b90f1eb6cdd7cff051ba964db598471556`.
- Old Ultima hybrid `minimap2.model` / new joint `minimap2_lr.model`:
  `4d2e556d2949e047bb7764ffbbb61af9f0d3ff3d750a7c17d7f6470e45550132`.
- Ultima pangenome `minimap2.model`:
  `20417e789fea9ff03063ad54cfe171cef5a75f0c1396c8875e3685abdc70ea99`.
- Joint Illumina pangenome `minimap2.model`:
  `9010b3423f5966dff2f1d05355ff40021aca56bc22ffcb2d6636acfffc476448`.

The Ultima bundle contributes only its mapper; its older graph/population
metadata does not describe the joint workflow. Record this composition
explicitly while validating joint graph/population against the joint bundle.
No byte-identity claim was established for the larger extraction models.

## Validation plan (not executed)

Focused cases: unchanged ILMN+ONT DAG; retained fork component/checkpoint/
finalization/gather interfaces; model routing; three RG channels; Ultima-only
filtering; missing/wrong models/references/population/sample/readgroups and
unsupported inputs rejected; failures/interruption and output indexes recorded.

Scientific evaluation: freeze same-donor Ultima/ONT data, coverage, truth,
regions, references and budget; compare against existing Ultima+ONT hybrid and
Ultima-only pangenome with matched inputs; report stratified SNP/indel precision
and recall, SV results, runtime/memory and model errors. Model incompatibility
is a recorded result, never authority to silently replace the joint model.

## G1 refresh review

Imported the common-ancestor→`v2.0.0` source patch with `git apply --3way
--index`; this is a source-refresh commit, not a branch merge. Resolved 22
conflicted files. Refactored vendor pipelines use upstream shared stages.
Upstream executor, pipeline and run-log implementations retain the fork's
failure/cleanup/process-group handling and add per-process/per-job metrics.
Preserved fork environment redaction in `shell_pipeline.py` and its regression
cases, rather than serializing inherited credentials into command logs.

Retained public commands: `dnascope`, `dnascope-longread`, `dnascope-hybrid`,
`dnascope-hybrid-finalize-contig`, `dnascope-hybrid-gather`, and
`dnascope-pangenome`/its existing alias; added upstream `hybrid-pangenome`.
Retained `--only_cnv`, `--only_svs`, disjoint `--haploid_bed` routing,
`--stop_after_model_apply`, component-specific required model validation,
optimized hybrid select/annotation/transfer scripts, and bounded finalization
thread budgets. Component-only CNV keeps its explicit two-BED route; ordinary
full hybrid uses upstream sex-aware CNV in its second DAG. Fork-only historical
ledgers, finalize/gather source, and regression modules are preserved.

Package metadata is `2.0.0+i.ultima.dev0` for this unreleased fork development
revision. No new Git tag or package publication. Source/diff inspection only;
no tests, lint, builds, CLI dry runs, or runtime execution were performed.
