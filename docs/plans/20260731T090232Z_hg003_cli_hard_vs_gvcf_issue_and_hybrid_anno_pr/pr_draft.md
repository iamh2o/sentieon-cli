# Speed up hybrid_anno.py with raw BGZF sharding

## Summary

This replaces full `vcflib.Variant` parsing in `hybrid_anno.py` with
coordinate-sharded raw BGZF record annotation while preserving the existing
command-line interface:

```text
hybrid_anno.py -v INPUT -b stage1_hap.bed -t THREADS \
  [--step-size BASES] OUTPUT
```

The replacement parses only the fields needed to assign `LHC`, keeps ordered
record ownership across shards, streams ordered fragments through `bgzip`, and
creates the tabix index once after successful output construction.

## Correctness

- Focused unit/oracle suite: 12 tests passed.
- Full upstream test suite: 137 tests passed.
- Doctest run: 137 tests passed.
- Flake8, Black check, and mypy: passed with the repository configuration.
- Compact fixtures cover BED boundaries/overlap, empty BED, missing contig
  lengths/indexes, invalid thread counts, gVCF records spanning shard
  boundaries, contig transitions, and unchanged command construction.
- Decompressed output and boundary tabix queries match the CLI 1.7.0 oracle at
  one and multiple threads.

PLACEHOLDER_CONTROL_EQUIVALENCE

## Performance

Existing full-data annotation-only benchmarks:

| Input | Threads | Original | Optimized | Reduction |
|---|---:|---:|---:|---:|
| Hard VCF | 128 | 14:55 | 0:18 | 98.0% |
| Hard VCF | 192 | 13:05 | 0:13 | 98.3% |
| gVCF | 128 | 59:21 | 3:21 | 94.4% |
| gVCF | 192 | 47:58 | 2:28 | 94.9% |

PLACEHOLDER_FRESH_BENCHMARK

The evidence records exact source commits, script hashes, commands, input
record counts, CPU time, peak RSS, and wall time.

## Scope

This PR changes only:

- `sentieon_cli/scripts/hybrid_anno.py`;
- focused tests;
- the minimal CI installation of `bgzip`/`tabix` needed for tool-backed tests.

It does not change Hybrid command construction, model application, population
transfer, hard-vs-gVCF semantics, DayOA, or HIOMR2.

Related investigation: PLACEHOLDER_ISSUE_URL
