Existing HG003 5x Illumina + 5x ONT evidence was found and reused before
launching any new compute. I filed the construction-path question separately as
[issue #29](https://github.com/Sentieon/sentieon-cli/issues/29).

For upstream CLI `v1.7.0` (`1bf377d`) with Sentieon Genomics `202503.03`, the
same completed CLI gVCF was evaluated directly and converted with:

```text
sentieon driver --reference REF --thread_count 32 --temp_dir TMP \
  --algo GVCFtyper -d DBSNP --vcf INPUT.g.vcf.gz \
  --emit_mode variant hard.raw.vcf.gz
```

All three lanes used identical HG003 GIAB v4.2.1 truth/BED/SDF and
`rtg vcfeval --decompose --squash-ploidy --ref-overlap`:

| Callset | TP call | FP | FN | Precision | Sensitivity | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Raw CLI gVCF | 3,604,748 | 17,651 | 227,142 | 0.9951 | 0.9407 | 0.9672 |
| GVCFtyper hard from that gVCF | 3,604,748 | 17,651 | 227,142 | 0.9951 | 0.9407 | 0.9672 |
| Native CLI hard | 3,603,895 | 17,202 | 227,997 | 0.9952 | 0.9405 | 0.9671 |

The raw-gVCF and GVCFtyper-hard `summary.txt` files are byte-identical
(`74c800d876398824ea989cb5278e79b4c86f2f48826224fc64da6e9cbf6a28e2`).
The native hard path differs. After `bcftools norm -f REF -m -both`, the
native-hard versus GVCFtyper-hard comparison has 953,551 native-only, 5,018
derived-only, and 4,773,983 shared records. Of the native-only records,
925,199 are `MLrejected`.

This existing result establishes the CLI 1.7.0 native-hard versus
gVCF-derived semantic distinction. It does **not** claim that this PR's gVCF
output has already been proven identical to upstream 1.7.0; that exact
upstream-versus-candidate gVCF A/B remains a separate validation boundary.
