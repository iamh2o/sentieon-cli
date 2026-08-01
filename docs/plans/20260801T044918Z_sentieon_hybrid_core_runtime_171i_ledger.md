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
  `origin/codex/hybrid-core-runtime-1.7.1i`; the first live runtime candidate
  was `0bf2b2f7f15ca75d14cc110af4fcd07086cd88da`. Live regression evidence then
  removed the selective normalizer, producing current reset candidate
  `501b57d48de49ec17e91fe1675ad3714c0d4173a`.
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
  Docker publication, force-push, or tag movement without later explicit user
  authorization. On 2026-08-01, after reviewing the completed matched HG003
  result, the user explicitly authorized the fork release and an upstream
  Sentieon PR. PyPI and Docker publication remain outside scope.

## 2026-08-01 release-gate amendment

The original release gate required eight full CLI lanes covering HG002 and
NA19235 in hard-VCF and gVCF modes. After the matched HG003 5x Illumina plus
5x ONT hard-VCF lane completed, the user explicitly directed publication based
on this result. That instruction supersedes the eight-lane gate for `1.7.1i`.
The unrun sample/mode matrix remains an explicit residual risk and is not
represented as completed evidence.

The amended release gate is:

- exact upstream `Sentieon/sentieon-cli` `v1.7.0` at `1bf377d` is the baseline;
- the optimized candidate retains the original final normalizer and includes
  only the selector, annotation, population-transfer, and scheduler-accounting
  changes;
- the matched HG003 hard-VCF lane must improve direct CLI wall time by at least
  20%;
- decompressed main, SV, and CNV record bodies, record counts, order, tabix
  contigs, and sampled tabix queries must match exactly;
- only run-specific provenance timestamps and scratch paths may differ;
- package version is `1.7.1+i`, annotated tag and GitHub Release are `1.7.1i`;
- no PyPI or Docker publication is authorized.

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
- Live lane status at the normalizer-reset decision:
  - Job `2464`, deployed iamh2o `c7d9fd4` reference: completed, 2,459 timed
    CLI seconds.
  - Job `2465`, first optimized candidate `0bf2b2f`: completed, 3,075 seconds.
    Main, SV, and CNV decompressed record bodies, counts, contig indexes, and
    sampled tabix queries exactly match job `2464`; volatile/provenance header
    classification remains in the harness. The 25.1% regression rejects the
    selective normalizer.
  - Job `2467`, exact upstream `v1.7.0` baseline `1bf377d`: completed with exit
    status 0; direct CLI wall time 3,485.27 seconds (58:05.27).
  - Job `2468`, reset candidate `501b57d` with the original final normalizer:
    completed with exit status 0 under the same `i128nvme`, `Comment=RnD`,
    one-node/task, 128-CPU contract; direct CLI wall time 2,510.35 seconds
    (41:50.35).

## HG003 release evidence

Both jobs consumed the same frozen SR and LR CRAMs prepared once from the
documented raw HG003 5x Illumina and 5x ONT FASTQs. GNU `time -v` surrounded
only the direct `sentieon-cli dnascope-hybrid` invocation; Slurm pending time,
raw-FASTQ preparation, publication, QC, and workflow-controller work are not
included.

| Measurement | Official 1.7.0 job 2467 | Optimized-reset job 2468 | Change |
|---|---:|---:|---:|
| Direct CLI wall time | 3,485.27 s | 2,510.35 s | -974.92 s (-27.97%) |
| Throughput ratio | 1.00x | 1.388x | +38.8% |
| User + system CPU time | 205,793.46 s | 192,456.76 s | -6.48% |
| Allocated 128-vCPU time | 123.92 vCPU-h | 89.26 vCPU-h | -27.97% |
| Mean process CPU reported by GNU time | 5,904% | 7,666% | +1,762 points |
| Maximum RSS | 45,840,108 KiB | 46,147,488 KiB | +0.67% |
| GNU-time filesystem inputs | 83,424,592 | 83,354,480 | -0.08% |
| GNU-time filesystem outputs | 244,870,072 | 245,269,592 | +0.16% |

The checked-in streaming comparison harness scanned the complete decompressed
record bodies and exercised the published tabix indexes:

| Product | Baseline records | Candidate records | Body SHA-256 | Contigs | Sampled tabix queries |
|---|---:|---:|---|---|---|
| Main hard VCF | 5,661,729 | 5,661,729 | exact | exact | exact |
| Long-read SV VCF | 15,847 | 15,847 | exact | exact | exact |
| CNV VCF | 2,942 | 2,942 | exact | exact | exact |

The raw header comparison differs only in `##SentieonCommandLine.*` execution
dates and job-specific `/scratch/...` paths. Command algorithms, arguments,
inputs, reference/model identifiers, field declarations, samples, and contig
metadata match. The final normalizer reported the same 5,661,729 total records
and 14,010 realigned records in both lanes.

## Control ledger

| ID | Area | Requirement | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| INV-001 | Source | Verify clean fresh checkout, exact base SHA, remotes, package state, and absence of branch/tag collisions | SUCCESS | contract_test | Gate 0 | orchestrator | Gate 0 inventory above; clean exact `e323d5e`; remote branch/tag probes |  | Exact isolated source boundary is frozen |
| AMEND-001 | Release gate | Record user authorization to release from the matched HG003 hard-VCF result instead of the original eight-lane matrix | SUCCESS | plan_amendment | Gate 6 | orchestrator | 2026-08-01 release-gate amendment above; jobs `2467` and `2468` |  | The broader matrix remains explicitly untested and is not claimed |
| BASE-001 | Live baseline | Freeze Take61 commands, HG002/NA19235 inputs, tool/model/reference/population versions, current timings, exact upstream 1.7.0 baseline, and deployed oracle reference | SUCCESS | contract_test | Gate 0 | orchestrator | Upstream `v1.7.0` verified as `1bf377d`; deployed iamh2o `c7d9fd4` retained only as a separate reference; exact matched official baseline job `2467` completed in 3,485.27 seconds | The shared 1.7.0 version string did not imply source identity; Git-object comparison found the iamh2o annotation optimization. | Exact official-source baseline is frozen and measured |
| ORACLE-001 | Differential tests | Build deterministic old-versus-new harnesses for selection, transfer, normalization, scheduler behavior, and failure atomicity | SUCCESS | contract_test | Gate 1 | orchestrator | Selector, annotation, transfer, normalization, scheduler-budget, index/query, and atomic-failure fixtures are green; jobs `2467`/`2468` provide full proprietary-publisher A/B proof | The local evidence environment omitted one legacy-only executable removed by this change; the exact deployed runtime supplied it for the oracle run. | Deterministic fixtures and live end-to-end output comparison pass |
| SELECT-001 | Hybrid selection | Replace the internal selector chain with direct indexed raw-VCF-to-BED generation | SUCCESS | feature_implementation | Gate 2 | orchestrator | Direct indexed raw-record-to-BED implementation, focused tests, exact legacy oracle differential, and live job `2468` | Object parsing plus three downstream processes scan and serialize avoidable intermediate data | Retained in release candidate |
| TRANSFER-001 | Population transfer | Replace 493 transfer jobs and concat with one bounded ordered transfer engine | SUCCESS | feature_implementation | Gate 2 | orchestrator | One bounded ordered job; exact old-pipeline differential covers unusual contigs, shard boundaries, Number=A/R/G, tabix, budgets, and atomic publication; live output bodies match job `2467` exactly | Hundreds of independently compressed/indexed shards amplify process, I/O, and DAG overhead | Retained with 32-worker cap proven by the matched live lane |
| NORM-001 | Final normalization | Preserve exact view semantics while selectively normalizing candidates and publishing once | NO_LONGER_NEEDED | feature_implementation | Gate 2 | orchestrator | The HG003 hard-VCF lane preserved exact record bodies but sent 1,110,521 of 5,661,729 records through 136 candidate batches. The optimized CLI took 3,075 seconds versus 2,459 seconds for the deployed iamh2o reference, a 616-second/25.1% regression; timing boundaries attribute approximately nine minutes of added wall time to the selective normalizer. The candidate script, command builder, and 325-line focused test module were removed, and the exact original `view -a` -> `norm -f` -> `vcfconvert` chain was restored for the next lane. | Candidate detection was much broader than actual realignment: the original normalizer reported only 14,010 realigned records, while Python orchestration and 136 subprocess batches dominated runtime. | Removed from release diff; original normalization retained |
| SCHED-001 | Scheduler | Correct thread claims for every multithreaded Python and fused job | SUCCESS | feature_implementation | Gate 2 | orchestrator | Selector, annotation, and transfer jobs claim full configured budgets; legacy final normalizer claims `min(3, cores)`; DAG non-overlap tests and live 128-CPU execution pass | Multithreaded Python jobs were declared as zero-thread scheduler work | Retained as scheduler correctness fix |
| NATIVE-001 | Native Sentieon | Profile pass 1, Stage1, Stage3, and pass 2; retain only parity-proven >=5% stage wins | NO_LONGER_NEEDED | feature_implementation | Gate 3 | orchestrator | No native Sentieon algorithm, interval, stage thread setting, or shard boundary is changed in the release; user directed release after the core-script result |  | No native candidate is present in the release diff |
| QA-001 | Local QA | Pass focused tests, complete tests/doctests, formatting, typing, build/install, and version checks | SUCCESS | contract_test | Gate 4 | orchestrator | Final functional suite and doctest invocation each report `153 passed, 1 skipped`; the single skip is the local-only legacy-bedtools selector oracle, which passed in the deployed headnode environment. CI-exact Black, Flake8, and mypy are green. Poetry 2.1.3 built `sentieon_cli-1.7.1+i` wheel and sdist in an isolated output directory. A separate target install resolved `sentieon_cli`, `hybrid_transfer.py`, and metadata from installed site-packages and reported `sentieon-cli --version` as `1.7.1+i`. `git diff --check` is green. |  | Final source, package, and installed CLI gates pass |
| SMOKE-001 | HG003 direct smoke | Run matched direct upstream-1.7.0/optimized hard-VCF jobs on HG003 raw 5x ILMN plus raw 5x ONT-derived frozen preparations | SUCCESS | contract_test | Gate 4 | orchestrator | Jobs `2467`/`2468`: exact upstream `1bf377d` 3,485.27 s versus reset candidate `501b57d` 2,510.35 s; exit 0; exact bodies for 5,661,729 main, 15,847 SV, and 2,942 CNV records; exact contigs and queries; only volatile provenance headers differ | Earlier installed/fork version strings did not prove source identity, so both source SHAs and imported module paths were frozen explicitly. | Amended live release gate passes with 27.97% wall-time reduction |
| DAYOA-001 | Downstream environment | If SMOKE-001 passes, create a new immutable HIOMR2 CLI environment YAML and update its explicit rule/profile references and tests | BLOCKED | config_or_startup_contract | Gate 4 | orchestrator | The completed live comparison emitted native hard VCF, not gVCF. The requested DayOA environment pin would govern both modes. After the release, the user explicitly asked whether the evidence was gVCF or VCF; no DayOA file was changed. | The only matched live proof is hard-VCF mode, so promoting the package to a shared hard/gVCF environment would extend beyond the proven semantic boundary. | Unblock with a matched upstream-1.7.0 versus 1.7.1i gVCF lane, or an explicit decision to accept the untested gVCF risk. The exact future pip entry is `sentieon-cli @ git+https://github.com/iamh2o/sentieon-cli.git@1.7.1i`. |
| LIVE-001 | Full CLI A/B | Complete eight direct core-CLI lanes: two samples by two modes by exact upstream-1.7.0 baseline/optimized | NO_LONGER_NEEDED | feature_implementation | Gate 5 | orchestrator | User-directed 2026-08-01 release-gate amendment; matched HG003 hard lane is complete |  | Not run and not claimed for `1.7.1i`; retained as residual follow-up evidence scope |
| PERF-001 | Acceptance | Prove semantic parity, >=20% median wall-time reduction, no lane >5% slower, and report CPU-hours/RSS/I/O | NO_LONGER_NEEDED | contract_test | Gate 5 | orchestrator | Original matrix gate superseded by AMEND-001; HG003 evidence table reports wall time, CPU time, RSS, and I/O and passes the amended >=20% threshold |  | Eight-lane median claim is not made |
| RELEASE-001 | Fork release | Merge validated fork PR, tag the clean merge commit, verify remote annotated tag, create the GitHub Release, and close the ledger | SUCCESS | feature_implementation | Gate 6 | orchestrator | Fork PR `iamh2o/sentieon-cli#1` merged normally as `e4f0ff8`; annotated tag object `085ad246` peels to that merge; GitHub Release `1.7.1i` published at `https://github.com/iamh2o/sentieon-cli/releases/tag/1.7.1i` |  | Fork release is published; no PyPI or Docker publication occurred |
| UPSTREAM-001 | Upstream PR | Open a focused PR to `Sentieon/sentieon-cli:main` for the retained runtime improvements | SUCCESS | feature_implementation | Gate 6 | orchestrator | Focused source/test commit `4dcf906` from exact upstream `1bf377d`; 153 passed, 1 expected local oracle skip; PR `https://github.com/Sentieon/sentieon-cli/pull/28` is open and mergeable |  | Upstream review is now owned by Sentieon maintainers |

## Candidate disposition rules

- A candidate becomes `SUCCESS` only when its retained code passes focused and
  full semantic gates.
- A candidate that changes semantics or lacks material gain is removed from
  the release diff and terminalized `NO_LONGER_NEEDED` with evidence.
- Scheduler accounting may be retained as a correctness repair when it has no
  direct standalone speed measurement, provided it introduces no regression.
- The original LIVE-001/PERF-001 publication rule is superseded only for
  `1.7.1i` by AMEND-001. The unrun matrix is not claimed.
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

## Publication closeout

- Fork PR: `https://github.com/iamh2o/sentieon-cli/pull/1`, merged normally at
  `2026-08-01T09:54:37Z` as
  `e4f0ff8bf4ddd882cb154774178d2b40babba056`.
- Annotated tag: `1.7.1i`; remote tag object
  `085ad246163eb8e220b66f52d11dcc241893b12f`, peeled commit
  `e4f0ff8bf4ddd882cb154774178d2b40babba056`.
- GitHub Release: `https://github.com/iamh2o/sentieon-cli/releases/tag/1.7.1i`,
  published `2026-08-01T09:55:38Z`.
- Upstream PR: `https://github.com/Sentieon/sentieon-cli/pull/28`; focused
  commit `4dcf906660215266ee9ad2121d7aed7113540557` is based directly on
  upstream `main` at `1bf377d3ce79fc4d8c2dc221e1f696441e38349d` and omits
  fork-specific release/version/evidence files.
- No PyPI, Docker, Slurm-administration, or DayOA workflow action occurred.
- The DayOA environment update is intentionally held because only native
  hard-VCF mode was tested; gVCF was not emitted by jobs `2467` or `2468`.

## Final report

All rows terminal: yes

Objective complete: no

The fork release and upstream-PR objectives are complete. The downstream
DayOA environment promotion is not complete because its shared hard/gVCF
runtime contract exceeds the completed hard-VCF-only evidence.

Status counts:

- SUCCESS: 11
- DUPLICATE: 0
- NO_LONGER_NEEDED: 4
- FAIL: 0
- BLOCKED: 1
- OPEN: 0
- IN_PROGRESS: 0
- ATTEMPTING_BUGFIX: 0
