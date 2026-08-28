# Sentieon CLI 1.7.4i Hybrid Stage-1 index and CNV combine ledger

## Objective

Correct the two caller defects observed in the released DayOA 16.0.18 HG002
5x Illumina by 5x ONT production-shaped run while preserving the public
`sentieon-cli dnascope-hybrid` boundary.

## Baseline evidence

| Row | State | Evidence |
|---|---|---|
| `BASE-001` | `SUCCESS` | Fork release `1.7.3i` peels to `50aeace1466682e8941ad24127256bbba36151b9`. |
| `BASE-002` | `SUCCESS` | Hybrid core reached `HybridStage2` and failed because `stage1_hap.bai` was absent beside `stage1_hap.bam`. |
| `BASE-003` | `SUCCESS` | Both XY CNVscope and ModelApply passes completed; the final `bcftools sort -Ou` to `sentieon util vcfconvert` pipe failed with `Too few fields at line 1`. |

## Execution ledger

| Row | Work | State | Terminal criterion |
|---|---|---|---|
| `CORE-001` | Index the Stage-1 haplotype BAM at the exact basename required by HybridStage2. | `IMPLEMENTED` | DAG contains `samtools index ... stage1_hap.bam stage1_hap.bai` between Stage 1 and Stage 2. |
| `CNV-001` | Send textual, reference-header-sorted VCF to Sentieon vcfconvert. | `IMPLEMENTED` | CNV combine uses `bcftools sort -Ov`; no BCF stream enters vcfconvert. |
| `VER-001` | Release the fork as immutable `1.7.4i`. | `SUCCESS` | This clean release commit is identified by the annotated pushed tag `1.7.4i`. |
| `DAY-001` | Pin `1.7.4i` through a new immutable DayOA environment contract. | `PENDING` | DayOA candidate dry run reaches attributable `rc=0` with zero submissions. |
| `RUN-001` | Resume the normal Bjuice plus Inflection targets in the existing HG002 capsule. | `PENDING` | Hybrid core and CNV receipts are `PASS`, packages validate, and controller/DayOA/Snakemake reach `rc=0`. |

## Boundaries

- Do not alter the Hybrid small-variant ploidy contract.
- Do not modify the released `1.7.3i` tag or a historical DayOA environment YAML.
- Do not add a recall DAG, raw workflow-level Sentieon driver call, or fallback.
- Do not export to S3, clean FSx, or intervene in Slurm.
