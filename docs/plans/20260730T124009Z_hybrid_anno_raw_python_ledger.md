# Hybrid annotation raw-Python implementation ledger

## Baseline

- Upstream source: Sentieon `sentieon-cli` tag `v1.7.0`
- Source commit: `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`
- Implementation branch: `codex/hybrid-anno-raw-python-v1.7.0`
- Local environment: `sentieon-cli-1.7.0-opt2`
- Runtime contract: Python 3.11, `vcflib` 1.0.1, HTSlib 1.24,
  bcftools 1.24
- Existing dirty LSMC Sentieon checkouts are explicitly out of scope.

## Ledger

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| INV-001 | Work from exact, clean `v1.7.0` | SUCCESS | Tag and commit recorded above |
| ENV-001 | Create isolated Conda environment with required tools | SUCCESS | `sentieon-cli-1.7.0-opt2` |
| IMP-001 | Preserve the existing command-line interface | SUCCESS | Focused command-builder test; `command_strings.py` unchanged |
| IMP-002 | Replace object parsing with raw sharded annotation | SUCCESS | Raw BGZF record processing with ordered coordinate shards |
| IMP-003 | Produce BGZF plus tabix index atomically | SUCCESS | Focused publication/index tests and full-data jobs |
| EQV-001 | Match decompressed single-thread oracle output | SUCCESS | Focused single-thread oracle comparison |
| EQV-002 | Match decompressed multi-thread oracle output | SUCCESS | Focused four-thread comparison and full-data 128/192-thread comparisons |
| EQV-003 | Preserve tabix query results and record order | SUCCESS | Focused boundary queries plus full-data oracle validation |
| PERF-001 | Benchmark hard VCF at 128 and 192 threads | SUCCESS | Annotation-only: 18 seconds at 128; 13 seconds at 192 |
| PERF-002 | Benchmark gVCF at 128 and 192 threads | SUCCESS | Annotation-only: 201 seconds at 128; 148 seconds at 192 |
| STOP-001 | Do not modify DayOA or HIOMR2 | SUCCESS | Final diff contains only this Sentieon CLI checkout |

## Fidelity correction

The first full-data run derived 9 Mb shards and changed an annotation. The first
difference was at `chr1:99000002`: the 9 Mb run emitted `LHC=1`, while the
untouched 1.7.0 oracle emitted `LHC=2`. The legacy interval lookup is
shard-boundary-sensitive, so the optimized implementation must retain both the
upstream 10,000,000-base default and `vcflib.Sharder.cut`'s cross-contig
boundary carry. Explicit `--step-size` remains supported.

The acceptance gate is semantic VCF parity, not byte identity: variants,
genotypes, samples, FILTER and INFO values (including `LHC`), order, and tabix
queries must agree. BGZF bytes and harmless header serialization may differ.

## Performance baselines

| Input | 128 threads | 192 threads | 90% reduction target |
|---|---:|---:|---:|
| Hard VCF | 14:55 | 13:05 | 1:30 / 1:19 |
| gVCF | 59:21 | 47:58 | 5:56 / 4:48 |

Correctness is mandatory. Missing the performance target does not authorize a
compiled implementation or a legacy fallback.

## Completed full-data proof

All four final annotation-only jobs completed RC 0 using the same replacement
script SHA-256
`887d281dcf9aba7513d268790fdd601cf7b4a904103226624fdd5403e2574f7e`.
Every output matched the untouched Sentieon CLI 1.7.0 oracle after
decompression, passed bgzip/tabix checks, preserved ordered tabix queries, and
reported the same record count.

| Input | Threads | Annotation time | Baseline | Reduction | Records |
|---|---:|---:|---:|---:|---:|
| Hard VCF | 128 | 18 seconds | 14:55 | 98.0% | 5,883,499 |
| Hard VCF | 192 | 13 seconds | 13:05 | 98.3% | 5,883,499 |
| gVCF | 128 | 201 seconds | 59:21 | 94.4% | 552,345,297 |
| gVCF | 192 | 148 seconds | 47:58 | 94.9% | 552,345,297 |
