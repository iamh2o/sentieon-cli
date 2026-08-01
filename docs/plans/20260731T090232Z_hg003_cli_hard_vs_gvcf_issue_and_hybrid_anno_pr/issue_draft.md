# Investigation: dnascope-hybrid native hard VCF differs from gVCF → GVCFtyper hard VCF in CLI 1.7.0

We are requesting clarification about the expected relationship between two
supported ways of obtaining a hard VCF from `dnascope-hybrid` in Sentieon CLI
1.7.0. This is an investigation request, not a claim of a confirmed defect.

## Result

On HG003 full-coverage Illumina + ONT data, the raw CLI gVCF and the hard VCF
created from that gVCF with `GVCFtyper --emit_mode variant` have identical
GIAB-HC RTG results. The native CLI hard-VCF mode is slightly better on the same
evaluation:

| Output | TP calls | FP | FN | F-score |
|---|---:|---:|---:|---:|
| CLI gVCF | 3,825,826 | 2,576 | 6,064 | 0.99887211 |
| GVCFtyper hard VCF from that gVCF | 3,825,826 | 2,576 | 6,064 | 0.99887211 |
| Native CLI hard VCF | 3,825,866 | 2,549 | 6,026 | 0.99888060 |

Native minus gVCF-derived is therefore:

- TP calls: `+40`
- TP baseline: `+38`
- FP: `-27`
- FN: `-38`
- F-score: `+0.00000849`

The attached directional tables enumerate both directions for every RTG
category; the values above are net deltas rather than an assertion that only
40, 27, or 38 loci changed.

## Construction-path and header differences

The native hard mode begins DNAscope in variant mode, applies the Hybrid model,
and finishes with:

```text
bcftools view -a -e GT="0/0"
```

The other route begins DNAscope in gVCF mode, completes the final gVCF
normalization, and then runs:

```text
sentieon driver -r REF -t THREADS \
  --algo GVCFtyper -d DBSNP --emit_mode variant \
  INPUT.g.vcf.gz OUTPUT.vcf.gz
```

The native hard VCF contains `LowQual` and `MLrejected` FILTER definitions,
plus `PL`, `MLEAC`, `MLEAF`, and `ML_PROB`. It contains 5,029,158 unfiltered
and 1,301,661 `MLrejected` records. The gVCF-derived hard VCF contains 5,026,771
unfiltered records and no ModelApply filter fields. Both contain the same
sample and zero hom-ref genotypes.

Full exact and semantic header diffs are linked below. Volatile command paths
and dates are reported separately from semantic `FILTER`, `INFO`, `FORMAT`,
contig, reference, and sample differences.

## Controlled CLI 1.7.0 reproduction

PLACEHOLDER_CONTROL_SUMMARY

The control used identical HG003 5× Illumina and ONT FASTQs, full-genome scope,
reference, HybridIlluminaONT2.0 model bundle, dbSNP, population VCF, Sentieon
Genomics 202503.03, and 128 threads for four lanes:

- untouched upstream CLI 1.7.0 native hard mode;
- untouched upstream CLI 1.7.0 gVCF followed by GVCFtyper;
- optimized-annotator fork native hard mode;
- optimized-annotator fork gVCF followed by the same GVCFtyper command.

The untouched upstream lanes establish whether the mode distinction exists
without the annotator optimization. Matched upstream/fork lanes establish
whether the optimized `hybrid_anno.py` changes any records, genotypes, FILTER,
INFO (including `LHC`), ordering, tabix queries, or RTG result.

## Differing records

PLACEHOLDER_CLASSIFICATION_SUMMARY

Complete compressed TSVs include normalized allele key, genotype, QUAL, FILTER,
variant type, `LHC`, `ML_PROB`, population annotations, source lane, and RTG
category. A separate full hard-VCF symmetric difference includes filtered
records and classifies presence/absence, genotype, representation or
multiallelic decomposition, ModelApply filtering, and annotation-only changes.

## Provenance

- Sentieon CLI: 1.7.0
- Upstream CLI commit: `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`
- Optimized fork commit used by the full-coverage run:
  `c7d9fd4ebad013ebc76052578e967f28d2e065e9`
- Sentieon Genomics: 202503.03
- Sample: HG003
- Reference: GRCh38 no-alt analysis set
- Model: HybridIlluminaONT2.0
- dbSNP: Homo_sapiens_assembly38.dbsnp138
- Population VCF: pop-v20g41-20251216
- RTG truth: GIAB HG003 v4.2.1 high-confidence
- Invalid Slurm 1768 evaluation: excluded
- Valid full-coverage lanes: CLI hard 1767, CLI gVCF RTG 1769, native-hard RTG
  1770, and the completed workflow GVCFtyper-derived RTG lane

Sanitized exact commands, versions, source hashes, resource paths/checksums,
scope checksum, Slurm provenance, and RTG command are in the evidence bundle.
No reads, alignments, references, model bundles, license material, credentials,
or retained scratch trees are shared.

## Private evidence links

The URLs below expire at `PLACEHOLDER_EXPIRY_UTC`.

PLACEHOLDER_PRESIGNED_URLS

Each S3 object has private ACLs, verified byte size, and SHA-256 metadata. The
linked manifest records the expected checksum for every object.

## Questions

1. Are native-hard and gVCF-derived filtering semantics intentionally
   different in `dnascope-hybrid` 1.7.0?
2. Is `GVCFtyper --emit_mode variant` the recommended conversion from a
   completed Hybrid gVCF?
3. If a user needs a hard VCF from a stored Hybrid gVCF that reproduces native
   hard-mode ModelApply filtering and annotations, is there an additional
   documented command or model application step?
4. Are the small GIAB-HC differences above expected from the two construction
   paths?
