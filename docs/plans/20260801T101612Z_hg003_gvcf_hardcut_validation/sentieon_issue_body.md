## Summary

This is a request for clarification about the intended semantics of two
supported DNAscope Hybrid output paths, not a claim of a confirmed Sentieon
defect.

On matched HG003 5x Illumina + 5x ONT input, the raw
`dnascope-hybrid --gvcf` output and a variants-only VCF produced from that gVCF
with Sentieon `GVCFtyper --emit_mode variant` have exactly the same GIAB RTG
vcfeval result. The VCF produced directly by `dnascope-hybrid` in native
hard-VCF mode is different, retains a large `MLrejected` audit trail, and has
slightly different vcfeval metrics.

## Environment

- Sentieon CLI: upstream `v1.7.0`, commit
  `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`
- Sentieon Genomics: `202503.03`
- Sample: HG003, slim-data 5x Illumina + 5x ONT
- Reference: GRCh38 no-alt analysis set
- Model: `HybridIlluminaONT2.0.bundle`
- dbSNP: `Homo_sapiens_assembly38.dbsnp138.vcf.gz`
- Population VCF: `pop-v20g41-20251216.vcf.gz`
- Truth/evaluation: GIAB HG003 v4.2.1 high-confidence VCF and BED

The native-hard and gVCF commands used the same SR/LR input data, reference,
model, dbSNP, population VCF, interval scope, Sentieon core, and sample name.

## gVCF-to-hard command

The completed gVCF was converted using:

```text
sentieon driver \
  --reference REF \
  --thread_count 32 \
  --temp_dir TMP \
  --algo GVCFtyper \
  -d DBSNP \
  --vcf INPUT.g.vcf.gz \
  --emit_mode variant \
  hard.raw.vcf.gz

bcftools sort -Oz -o hard.vcf.gz hard.raw.vcf.gz
bcftools index --tbi hard.vcf.gz
```

The published derived hard VCF SHA-256 was:

```text
050f0f5f9a88d8ff84b2e9cc10492010a272b76da3ba3ffdf3707f2e5551f082
```

## Three-way vcfeval result

Every lane used the same contract:

```text
rtg vcfeval --decompose --squash-ploidy --ref-overlap \
  -e HG003.bed -b HG003.vcf.gz -c CALLSET -o OUT \
  -t Homo_sapiens_assembly38.fasta.sdf --threads N
```

| Callset | TP baseline | TP call | FP | FN | Precision | Sensitivity | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Raw CLI gVCF | 3,604,773 | 3,604,748 | 17,651 | 227,142 | 0.9951 | 0.9407 | 0.9672 |
| GVCFtyper hard VCF from that gVCF | 3,604,773 | 3,604,748 | 17,651 | 227,142 | 0.9951 | 0.9407 | 0.9672 |
| Native CLI hard VCF | 3,603,918 | 3,603,895 | 17,202 | 227,997 | 0.9952 | 0.9405 | 0.9671 |

The raw-gVCF and GVCFtyper-hard `summary.txt` files are byte-identical,
SHA-256:

```text
74c800d876398824ea989cb5278e79b4c86f2f48826224fc64da6e9cbf6a28e2
```

A duplicate raw-gVCF vcfeval at a different thread count also produced that
exact summary.

## Direct native-hard versus GVCFtyper-hard comparison

After `bcftools norm -f REF -m -both`:

| Record class | Native-hard only | GVCFtyper-hard only | Shared |
|---|---:|---:|---:|
| All records | 953,551 | 5,018 | 4,773,983 |
| Accepted (`PASS,.`) | 28,352 | 27,649 | 4,751,352 |

Of the 953,551 native-hard-only records:

- 925,199 have `FILTER=MLrejected`
- 28,352 have `FILTER=.`

The raw gVCF and GVCFtyper-hard headers contain `INFO/LHC`, but no
`FILTER/MLrejected` or `FILTER/LowQual` definition. The native hard VCF
contains those filter definitions and rejected records.

One retained intermediate example is `chr1:10057`:

- gVCF ModelApply intermediate: `A -> G,<NON_REF>`, `GT=0/0`, `LHC=1`,
  `FILTER=.`
- final gVCF normalization removes the unused ALT
- native hard mode: `A -> G`, `GT=0/1`, `LHC=1`, `FILTER=MLrejected`

This suggests that a later GVCFtyper invocation cannot reconstruct the native
hard-mode rejection record after the ALT/genotype has been collapsed.

## Questions

1. Are the native-hard and gVCF-derived filtering semantics intentionally
   different for `dnascope-hybrid`?
2. Is `GVCFtyper --emit_mode variant` the recommended way to obtain a hard VCF
   from a completed Hybrid gVCF?
3. If a stored Hybrid gVCF must be converted into a hard VCF that preserves the
   native hard-mode ModelApply rejection trail and annotations, is there an
   additional supported command or required ordering?
4. Are the small vcfeval differences above expected from the two construction
   paths?

The exact manifests, RTG bundles, direct-comparison counts, intermediate locus
evidence, and job logs are retained and can be shared privately if useful.
