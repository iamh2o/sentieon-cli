# Sentieon Hybrid CLI 1.7.1i core-runtime optimization ledger

## Objective

Optimize only the `iamh2o/sentieon-cli` 1.7.0 Hybrid CLI core while preserving
semantic output. Retain only parity-proven material wins, require at least a
20% median end-to-end wall-time reduction across HG002 and NA19235 in both
hard-VCF and gVCF modes, merge the validated fork PR, and publish the exact
annotated tag `1.7.1i` for package version `1.7.1+i`.

## Gate 0 inventory freeze

- Controlling ledger and plan:
  `docs/plans/20260801T044918Z_sentieon_hybrid_core_runtime_171i_ledger.md`
- Fresh checkout:
  `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-core-runtime-1.7.1i`
- Work branch: `codex/hybrid-core-runtime-1.7.1i`
- Exact branch base: `iamh2o/codex/hybrid-anno-opt2-v1.7.0` at
  `e323d5e05c60961ac182b32b633681fb919759ec`
- Deployed code oracle:
  `c7d9fd4ebad013ebc76052578e967f28d2e065e9`; the four commits between the
  oracle and branch base add evidence only.
- Upstream 1.7.0 source: `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`.
- Fork default branch: `iamh2o/sentieon-cli:main`.
- Pushed candidate commit:
  `bddecacee15d0aec922f4a9e7782b877366beb14` on
  `origin/codex/hybrid-core-runtime-1.7.1i`.
- `codex/hybrid-core-runtime-1.7.1i`, tag `1.7.1i`, and tag `v1.7.1i` were
  absent remotely at Gate 0.
- Fresh checkout status: clean on the work branch.
- Existing evidence checkout
  `/Users/jmajor/projects/cli_refactor/sentieon-cli-hybrid-anno-v1.7.0` has an
  intentional modified evidence ledger and is outside this task's write scope.
- Local pinned test environment: `sentieon-cli-1.7.0-opt2`, Python 3.11,
  bcftools/HTSlib 1.24.
- Baseline tests:
  - `pytest -q tests/unit/test_hybrid_anno.py` -> `12 passed in 0.63s`.
  - `pytest -q` -> `137 passed in 0.85s`.
  - `git diff --check` -> RC 0.
- Source sweep:
  - 16 relevant selector/transfer/normalization call sites.
  - 12 zero-thread Hybrid job declarations or arguments requiring
    classification.
- Measured Take61 core baseline after excluding DayOA wrapper sleeps:
  HG002 154.8m, HG004 167.4m, NA19235 181.9m, NA20775 102.5m; mean 151.6m.
- Final gVCF records: HG002 297,241,525; HG004 306,521,305; NA19235
  433,405,159; NA20775 217,565,390.
- Core implementation boundary: no QC/MultiQC/mosdepth, no
  SV/CNV/Inflection work, no wrapper sleeps, no raw Snakemake, and no Slurm
  administration. Live acceptance uses direct core CLI jobs only. Per the
  subsequent user instruction, a parity- and performance-passing HG003 smoke
  authorizes a separate DayOA change that creates a new immutable HIOMR2 CLI
  environment YAML and updates the explicit rule/config references; the
  existing versioned YAML must not be edited in place.
- Semantic parity means matching decompressed record bodies, samples, contigs,
  order, GT, QUAL, FILTER, INFO including `LHC`, population fields,
  `MLrejected`, `END`, `AC`, and `AN`, plus BGZF/tabix query behavior.
  Compressed bytes and explicitly classified volatile provenance/version
  header lines may differ.
- Publication boundary: no upstream Sentieon PR, GitHub Release, PyPI upload,
  Docker publication, force-push, or tag movement.

## HG003 direct-CLI smoke and downstream promotion gate

- Input contract: raw slim-data HG003 5x paired Illumina FASTQs plus raw HG003
  5x ONT FASTQ. No source CRAM may substitute for the ONT FASTQ.
- Illumina R1:
  `/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/NovaSeqX_WHGS_TruSeqPF_HG002-007/downsampled/HG003_5x_R1.fastq.gz`
  (3,902,280,885 bytes; SHA-256
  `f71e9a78961dcbea61b6e11f4c89fbc7df85300708ea1de02f176bc7ff212055`).
- Illumina R2:
  `/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/NovaSeqX_WHGS_TruSeqPF_HG002-007/downsampled/HG003_5x_R2.fastq.gz`
  (4,023,184,443 bytes; SHA-256
  `a60f04dc59a549e7f6a7d5ca78528004712fcb3f7dbdfd2bab3ddc865dbc0bb6`).
- ONT FASTQ:
  `/fsx/references/genomic_data/organism_reads_slim/fastq/H_sapiens/giab/agbt_2026/ont/HG003_5x.cleaned.primary.fastq.gz`
  (6,685,453,565 bytes; SHA-256
  `93b0adac68dc4ce3c1127e3bd0a97f71abc69c55e5dd56fa00c7409d6f9c8637`).
- Build one SR prepared CRAM and one LR aligned CRAM from those raw FASTQs,
  using the same reference, model members, read groups, and Sentieon
  202503.03 preparation contract for both candidates. Freeze and reuse those
  two alignment products so measured wall time begins at the direct Hybrid CLI
  invocation.
- Run the exact deployed oracle `c7d9fd4` and the optimized candidate as two
  independent direct commands submitted with
  `sbatch --partition i128nvme --comment RnD --cpus-per-task=128`; no DayOA
  controller or QC target is in either timed lane.
- The smoke is full primary assembly (`chr1`-`chr22`, `chrX`, `chrY`, `chrM`)
  and initially compares native hard-VCF mode. The original hard/gVCF release
  matrix remains required before tagging `1.7.1i`.
- The downstream DayOA environment pin changes only if record-body/header,
  index/query, and required side-product parity pass and the optimized core
  lane shows a material wall-time win without higher failure risk.

## Control ledger

| ID | Area | Requirement | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| INV-001 | Source | Verify clean fresh checkout, exact base SHA, remotes, package state, and absence of branch/tag collisions | SUCCESS | contract_test | Gate 0 | orchestrator | Gate 0 inventory above; clean exact `e323d5e`; remote branch/tag probes |  | Exact isolated source boundary is frozen |
| BASE-001 | Live baseline | Freeze Take61 commands, HG002/NA19235 inputs, tool/model/reference/population versions, current timings, and deployed oracle | IN_PROGRESS | contract_test | Gate 0 | orchestrator | Exact oracle and current measured timing/record baselines frozen above; live command/input path inventory pending |  |  |
| ORACLE-001 | Differential tests | Build deterministic old-versus-new harnesses for selection, transfer, normalization, scheduler behavior, and failure atomicity | ATTEMPTING_BUGFIX | contract_test | Gate 1 | orchestrator | Transfer and normalization differentials are green; deployed-selector comparison reached the legacy slop step but the pinned local test environment lacks `bedtools`; exact existing runtime binary lookup pending | Local evidence environment omitted one legacy-only executable removed by this change |  |
| SELECT-001 | Hybrid selection | Replace the internal selector chain with direct indexed raw-VCF-to-BED generation | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | Direct indexed raw-record-to-BED implementation and six focused tests are green; full oracle and live timing pending | Object parsing plus three downstream processes scan and serialize avoidable intermediate data |  |
| TRANSFER-001 | Population transfer | Replace 493 transfer jobs and concat with one bounded ordered transfer engine | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | One full-budget DAG job now runs bounded ordered merge/trim workers and one BGZF/index publisher; exact old-pipeline differential, unusual-contig, shard-boundary, Number=A/R/G, tabix, budget, and atomic validation tests: `12 passed`; live cap sweep pending | Hundreds of independently compressed/indexed shards amplify process, I/O, and DAG overhead |  |
| NORM-001 | Final normalization | Preserve exact view semantics while selectively normalizing candidates and publishing once | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | Bounded ordinal-batch implementation: full `view -a`, direct pass-through REF validation including `<NON_REF>` blocks, selective `norm -f`, original-position restoration, marker stripping, and one BGZF/tabix publication. Hard/gVCF fixture bodies, semantic headers, indexes, and queries match the full pipeline; the fixture proves exactly three real normalization candidates while two hom-reference blocks bypass `norm`. Proprietary `vcfconvert` and live timing proof remain. | Full gVCF record stream was parsed and serialized by view, norm, and vcfconvert even when representation could not change |  |
| SCHED-001 | Scheduler | Correct thread claims for every multithreaded Python and fused job | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | Selector, annotation, transfer, and normalization jobs claim the full configured core budget; DAG non-overlap tests pass. Fused transfer budgets two processes per merge/trim worker plus the final BGZF publisher within the claimed allocation. Live scheduler observation remains. | Multithreaded Python jobs were declared as zero-thread scheduler work |  |
| NATIVE-001 | Native Sentieon | Profile pass 1, Stage1, Stage3, and pass 2; retain only parity-proven >=5% stage wins | OPEN | feature_implementation | Gate 3 | orchestrator | Pending |  |  |
| QA-001 | Local QA | Pass focused tests, complete tests/doctests, formatting, typing, build/install, and version checks | IN_PROGRESS | contract_test | Gate 4 | orchestrator | Functional and doctest suite `160 passed`; CI-exact Black, focused new-script Black, Flake8, and mypy are green. Poetry 2.1.3 built the 1.7.0 wheel and sdist in an isolated temporary environment; the wheel installed successfully into a separate target, reported `sentieon-cli 1.7.0`, and resolved the three new runtime scripts from installed site-packages. The pre-gate version intentionally remains 1.7.0; final post-profile rerun and 1.7.1+i version proof remain. |  |  |
| SMOKE-001 | HG003 direct smoke | Run matched direct oracle/optimized hard-VCF jobs on HG003 raw 5x ILMN plus raw 5x ONT-derived frozen preparations | IN_PROGRESS | contract_test | Gate 4 | orchestrator | Dedicated locked root `/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x`; write visit and lock acquired by `codex-sentieon-cli-171i-20260801`; exact input paths, byte sizes, and SHA-256 values frozen above. Remote source is clean at pushed candidate `bddecace`; deployed-oracle prefix proves direct URL commit `c7d9fd4`. The full-primary BED has 25 contigs and SHA-256 `6f6179a3bc159e9527a56e665f8e5363fb8ee4af58696fbbdd043d1e0df6128d`. Raw preparation job `2457` and dependency-held direct jobs `2458` (oracle) and `2459` (optimized) were submitted with `--partition i128nvme --comment RnD --cpus-per-task=128`; `2457` reached RUNNING on `i128nvme-dy-price128nvme-2`. |  |  |
| DAYOA-001 | Downstream environment | If SMOKE-001 passes, create a new immutable HIOMR2 CLI environment YAML and update its explicit rule/profile references and tests | OPEN | feature_implementation | Gate 4 | orchestrator | User authorization recorded; no DayOA file changed before the smoke gate |  |  |
| LIVE-001 | Full CLI A/B | Complete eight direct core-CLI lanes: two samples by two modes by baseline/optimized | OPEN | feature_implementation | Gate 5 | orchestrator | Pending |  |  |
| PERF-001 | Acceptance | Prove semantic parity, >=20% median wall-time reduction, no lane >5% slower, and report CPU-hours/RSS/I/O | OPEN | contract_test | Gate 5 | orchestrator | Pending |  |  |
| RELEASE-001 | Fork release | Merge validated fork PR, tag the clean merge commit, verify remote annotated tag, and close the ledger | OPEN | feature_implementation | Gate 6 | orchestrator | Pending |  |  |

## Candidate disposition rules

- A candidate becomes `SUCCESS` only when its retained code passes focused and
  full semantic gates.
- A candidate that changes semantics or lacks material gain is removed from
  the release diff and terminalized `NO_LONGER_NEEDED` with evidence.
- Scheduler accounting may be retained as a correctness repair when it has no
  direct standalone speed measurement, provided it introduces no regression.
- No merge or tag occurs unless LIVE-001 and PERF-001 are `SUCCESS`.
- If the release gate cannot pass, the branch and terminal ledger remain as
  evidence; fork `main` and all tags remain unchanged.

## Native profiling matrix

- Pass 1 and pass 2 thread counts: `64`, `96`, `128`.
- Stage3 driver/sort allocations: `64/64`, `96/32`, `32/96`, `128/128`.
- Stage1 `(ins,hap,bwa,sort)` allocations: baseline `128/128/128/128`, then
  `16/48/32/32`, `16/64/32/16`, `16/32/64/16`, and `16/32/16/64`.
- Each candidate runs twice on a fixed 128-vCPU node and frozen intermediates.
- Retain only exact-parity candidates with at least 5% median stage reduction;
  within 2%, choose lower allocated vCPU-hours.

## Final report

All rows terminal: no

Objective complete: no

Status counts:

- SUCCESS: 1
- DUPLICATE: 0
- NO_LONGER_NEEDED: 0
- FAIL: 0
- BLOCKED: 0
- OPEN: 5
- IN_PROGRESS: 7
- ATTEMPTING_BUGFIX: 1
