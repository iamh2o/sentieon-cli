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
- Upstream 1.7.0 source: `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`;
  the live upstream `Sentieon/sentieon-cli` `v1.7.0` ref and the local tag both
  resolve to this commit. The deployed iamh2o oracle is one runtime commit
  ahead and is therefore a separate reference, not the stock baseline.
- Fork default branch: `iamh2o/sentieon-cli:main`.
- Pushed candidate commit:
  `bddecacee15d0aec922f4a9e7782b877366beb14` on
  `origin/codex/hybrid-core-runtime-1.7.1i`; evidence-only selector-oracle and
  Slurm-harness follow-ups advance the branch tip to
  `fec179c8e0e98fffc09621fb4f8b59f7a074b1bc` without changing runtime code
  after `0bf2b2f7f15ca75d14cc110af4fcd07086cd88da`.
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
- Run exact upstream Sentieon `v1.7.0` commit `1bf377d` and the optimized
  candidate as two independent direct commands submitted with
  `sbatch --partition i128nvme --comment RnD --cpus-per-task=128`; no DayOA
  controller or QC target is in either timed lane. Retain the completed
  deployed-iamh2o-oracle `c7d9fd4` lane as an informative third reference, but
  do not label or use it as the stock baseline because it already contains the
  accelerated `hybrid_anno.py` implementation.
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
| BASE-001 | Live baseline | Freeze Take61 commands, HG002/NA19235 inputs, tool/model/reference/population versions, current timings, exact upstream 1.7.0 baseline, and deployed oracle reference | IN_PROGRESS | contract_test | Gate 0 | orchestrator | Upstream `v1.7.0` is verified as `1bf377d`; deployed iamh2o `c7d9fd4` is exactly one runtime commit ahead and is retained only as a separate reference. Current measured timing/record baselines are frozen above; remaining live command/input path inventory is pending. | The shared 1.7.0 version string did not imply source identity; Git-object comparison found the iamh2o annotation optimization. |  |
| ORACLE-001 | Differential tests | Build deterministic old-versus-new harnesses for selection, transfer, normalization, scheduler behavior, and failure atomicity | IN_PROGRESS | contract_test | Gate 1 | orchestrator | Transfer and normalization differentials are green. The deployed headnode oracle environment supplied legacy bedtools 2.31.1; the checked-in exact vcflib object filter -> `bcftools view` -> `bcftools query` -> `bedtools slop` differential passed against the direct selector. Scheduler-budget and atomic-failure fixtures are green; final proprietary-publisher/full-output A/B proof remains. | The local evidence environment omitted one legacy-only executable removed by this change; the exact deployed runtime resolved it without changing the candidate. |  |
| SELECT-001 | Hybrid selection | Replace the internal selector chain with direct indexed raw-VCF-to-BED generation | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | Direct indexed raw-record-to-BED implementation and six focused tests are green; full oracle and live timing pending | Object parsing plus three downstream processes scan and serialize avoidable intermediate data |  |
| TRANSFER-001 | Population transfer | Replace 493 transfer jobs and concat with one bounded ordered transfer engine | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | One full-budget DAG job now runs bounded ordered merge/trim workers and one BGZF/index publisher; exact old-pipeline differential, unusual-contig, shard-boundary, Number=A/R/G, tabix, budget, and atomic validation tests: `12 passed`; live cap sweep pending | Hundreds of independently compressed/indexed shards amplify process, I/O, and DAG overhead |  |
| NORM-001 | Final normalization | Preserve exact view semantics while selectively normalizing candidates and publishing once | NO_LONGER_NEEDED | feature_implementation | Gate 2 | orchestrator | The HG003 hard-VCF lane preserved exact record bodies but sent 1,110,521 of 5,661,729 records through 136 candidate batches. The optimized CLI took 3,075 seconds versus 2,459 seconds for the deployed iamh2o reference, a 616-second/25.1% regression; timing boundaries attribute approximately nine minutes of added wall time to the selective normalizer. The candidate script, command builder, and 325 focused tests were removed, and the exact original `view -a` -> `norm -f` -> `vcfconvert` chain was restored for the next lane. | Candidate detection was much broader than actual realignment: the original normalizer reported only 14,010 realigned records, while Python orchestration and 136 subprocess batches dominated runtime. | Removed from release diff; original normalization retained |
| SCHED-001 | Scheduler | Correct thread claims for every multithreaded Python and fused job | IN_PROGRESS | feature_implementation | Gate 2 | orchestrator | Selector, annotation, and transfer worker jobs claim the full configured core budget; DAG non-overlap tests pass. Fused transfer budgets two processes per merge/trim worker plus the final BGZF publisher within the claimed allocation. After resetting final normalization, its three-process legacy pipeline claims `min(3, cores)` rather than zero. Focused DAG tests: `18 passed`; live scheduler observation remains. | Multithreaded Python jobs were declared as zero-thread scheduler work |  |
| NATIVE-001 | Native Sentieon | Profile pass 1, Stage1, Stage3, and pass 2; retain only parity-proven >=5% stage wins | OPEN | feature_implementation | Gate 3 | orchestrator | Pending |  |  |
| QA-001 | Local QA | Pass focused tests, complete tests/doctests, formatting, typing, build/install, and version checks | IN_PROGRESS | contract_test | Gate 4 | orchestrator | After adding the exact selector oracle, the functional and doctest suite reports `160 passed, 1 skipped`; the skip is only the unavailable local legacy bedtools executable, and the same test passed on the deployed headnode runtime. CI-exact Black, focused new-script/test Black, Flake8, and mypy are green. Poetry 2.1.3 built the 1.7.0 wheel and sdist in an isolated temporary environment; the wheel installed successfully into a separate target, reported `sentieon-cli 1.7.0`, and resolved the three new runtime scripts from installed site-packages. The pre-gate version intentionally remains 1.7.0; final post-profile rerun and 1.7.1+i version proof remain. |  |  |
| SMOKE-001 | HG003 direct smoke | Run matched direct upstream-1.7.0/optimized hard-VCF jobs on HG003 raw 5x ILMN plus raw 5x ONT-derived frozen preparations | IN_PROGRESS | contract_test | Gate 4 | orchestrator | Dedicated locked root `/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x`; write visit and lock acquired by `codex-sentieon-cli-171i-20260801`; exact input paths, byte sizes, and SHA-256 values frozen above. Remote source is clean at pushed runtime candidate `0bf2b2f`; deployed-oracle prefix proves direct URL commit `c7d9fd4`. The full-primary BED has 25 contigs and SHA-256 `6f6179a3bc159e9527a56e665f8e5363fb8ee4af58696fbbdd043d1e0df6128d`. Raw preparation job `2457` completed in 535 seconds and atomically published a 2.0 GiB indexed SR CRAM plus 3.4 GiB indexed LR CRAM; joint `samtools quickcheck` passed. Initial direct jobs `2458`/`2459` exposed a pre-CLI Slurm-spool companion-asset path bug and published no result. Job `2464` then completed successfully in 2,459 timed CLI seconds, but Git-object verification proved it was the already annotation-optimized iamh2o `c7d9fd4` deployment; it is reclassified as an informative fork reference and will not be used as the stock baseline. Job `2465` is the optimized candidate. Replacement job `2467` uses a detached, clean upstream `v1.7.0` checkout at `1bf377d`, directly invokes the CLI with that checkout first on `PYTHONPATH`, and atomically publishes under `results/official170/hard`. Its preflight proved the exact imported module path and version `1.7.0`; Slurm confirmed `i128nvme`, `Comment=RnD`, one node/task, 128 CPUs, and a four-hour limit. | The installed CLI identified itself only as 1.7.0 even though its direct-URL source was one commit beyond upstream. Slurm also copies submitted scripts to `/var/spool/slurmd`, so neighboring assets must use exact locked paths. |  |
| DAYOA-001 | Downstream environment | If SMOKE-001 passes, create a new immutable HIOMR2 CLI environment YAML and update its explicit rule/profile references and tests | OPEN | feature_implementation | Gate 4 | orchestrator | User authorization recorded; no DayOA file changed before the smoke gate |  |  |
| LIVE-001 | Full CLI A/B | Complete eight direct core-CLI lanes: two samples by two modes by exact upstream-1.7.0 baseline/optimized | OPEN | feature_implementation | Gate 5 | orchestrator | Pending |  |  |
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
- IN_PROGRESS: 8
- ATTEMPTING_BUGFIX: 0
