# Experimental Ultima + ONT hybrid-pangenome calling

This fork adds `--experimental_ultima` to upstream `hybrid-pangenome`.
It uses the new joint pangenome workflow with an Ultima mapping model and the
released **Illumina+ONT joint calling model**. Accuracy for this combination
has not been established. Source implementation, functional execution,
scientific evaluation, and production acceptance are separate states.

The implementation is based on [Sentieon CLI v2.0.0](https://github.com/Sentieon/sentieon-cli/tree/a0016609f411f1656bd29617a2344a0a97fe5ea9),
integrated into fork `1.7.7i`. The development package version is
`2.0.0+i.ultima.dev0`; it is not a published release. The fork retains
component-only hybrid calls, the model-apply checkpoint, contig finalization
and gather, optimized hybrid VCF processing, and lifecycle fixes. Fork release
`2.0.2` supersedes that development package for the approved HG002 campaign.
Focused checks on the verified `ashg-etc` headnode passed 218 cases on
2026-10-20; scientific and production acceptance remain separate.

## Driver and model assets

An existing Sentieon **202503.04 or later** installation meets the driver
minimum; this does not require a new proprietary driver implementation.
The wrapper needs the new hybrid-pangenome joint bundle and matching reference
assets. Existing Ultima mapping assets can be reused if they match the profile.
The [vendor model registry](https://github.com/Sentieon/sentieon-models/blob/main/sentieon_models.yaml)
publishes separate Ultima pangenome and Ultima+ONT hybrid bundles; the selected
joint pangenome bundle is the Illumina+ONT one.

| Role | Immutable vendor member |
|---|---|
| Joint DNAscope and DNAModelApply | `HybridPangenomeIlluminaONT1.0.bundle/dnascope.model` |
| Read extraction | Same joint bundle, `extract.model` |
| ONT LongReadSV | Same joint bundle, `longreadsv.model` |
| Ultima graph realignment/liftover | `SentieonUltimaPangenomeRealignWGS1.3.bundle/minimap2.model` |
| Graph | `hprc-v2.1-mc-grch38.gbz` |
| Haplotype index | `hprc-v2.1-mc-grch38.hapl` |
| Population annotations | Indexed VCF with `SentieonVcfID=population-hprc-v2.0-20260528` |

`-m` always selects the joint bundle. `--sr_model_bundle` selects only the
Ultima mapper. The older graph/population metadata inside the Ultima bundle
is preserved verbatim and is **not** used to choose the joint reference set.
The CLI validates both metadata profiles and the measured SHA256 of the
released Ultima mapper and ONT SV model. The receipt records SHA256 for both
complete bundles and each used member; no bundle is rewritten or repacked.

The normal upstream dependencies remain: Python 3.11+, Sentieon, samtools
1.16+, bcftools 1.22+, bedtools, vg, and Sentieon's patched KMC with stdin
support. Install this checkout in the intended execution environment using
the repository's normal Python packaging flow. No installation or workflow
launch is performed by this documentation.

## Input contract

- Supply one donor's aligned, coordinate-sorted, indexed Ultima BAM/CRAM files
  through `--sr_aln`, and aligned, indexed ONT files through `--lr_aln`.
- Ultima data must already be duplicate-marked or deduplicated. The CLI
  requires an `@PG` record identifying Sentieon Dedup, MarkDuplicates, or
  markdup. This is header evidence; it does not inspect every record to prove
  duplicate marking or verify biological donor identity.
- Each input needs valid `@RG ID`, `SM`, and `PL` tags. `PL` must be `ULTIMA`
  for short reads and `ONT` for long reads (case-insensitive). All `SM` values
  must agree. IDs must be unique across every input; the first Ultima ID plus
  `-pg` is reserved for the lifted reads. Driver routing delimiters in IDs
  are rejected. The `--rgsm` override is unavailable in this mode.
- Every alignment's ordered `@SQ SN/LN` dictionary must equal the supplied
  FASTA `.fai`. Conflicting `M5` sequence checksums are rejected when present
  in the alignment headers. The FASTA must identify as GRCh38.
- Supply the named GBZ/HAPL pair above. The CLI checks actual GRCh38 graph
  metadata, HAPL k=29/chain structure, fixed observed GBZ/HAPL content hashes, backbone presence, population ID and
  contig lengths. Naming and structural consistency do not certify vendor
  content: no vendor-signed GBZ/HAPL checksum manifest was supplied; the pinned
  content hashes were observed from the selected vendor download pair. Preserve the source/download provenance of the pair for
  the scientific evaluation.
- Alignment indexes may use native adjacent `.bai`, `.csi`, or `.crai`
  naming. Population annotations require an adjacent `.tbi` or `.csi`.
  Missing assets fail; the CLI does not download, repair, or substitute them.

FASTQ/uBAM processing, ONT realignment, CNV/segdup/ExpansionHunter/T1K calling,
sample-sex overrides, partial caller branches, and gVCF are outside this
profile. Model, tool-version, population, and reference checks cannot be
disabled. Use a fresh output prefix and log directory for each invocation;
existing outputs or provenance receipts are never overwritten.

## Invocation

Illustrative paths only; replace them with explicitly selected assets before
execution. Runtime evaluation remains a separate authorization gate.

```bash
sentieon-cli hybrid-pangenome /analysis/ug_ont_pg.vcf.gz \
  --experimental_ultima \
  --sr_model_bundle /models/SentieonUltimaPangenomeRealignWGS1.3.bundle \
  -m /models/HybridPangenomeIlluminaONT1.0.bundle \
  -r /references/GRCh38.fa \
  --gbz /references/hprc-v2.1-mc-grch38.gbz \
  --hapl /references/hprc-v2.1-mc-grch38.hapl \
  --pop_vcf /references/population-hprc-v2.0-20260528.vcf.gz \
  --sr_aln /inputs/donor.ultima.markdup.cram \
  --lr_aln /inputs/donor.ont.cram \
  -b /references/evaluation_regions.bed \
  -t 32
```

Supply `--pcr_free` only when appropriate to the input library, and
`--bam_format` for lifted BAM output. `--dry_run` performs real input/asset
preflight, including header reads, bundle hashing, tool/version checks and
the upstream KMC capability probe, then prints pipeline commands. It writes
a `dry_run` provenance receipt and does not claim completed callsets. Use a
separate fresh prefix for an authorized live invocation.

The BED restricts small-variant calling. Following upstream behavior, graph
construction, ONT LongReadSV and PangenomeSV still process their full inputs;
supplying a small BED alone does **not** bound whole-workflow cost.

## Workflow and read-group channels

1. Joint Ultima/ONT k-mer counting builds a personalized pangenome.
2. ONT alignments update the graph; LongReadSV supplies additional update regions.
3. Extracted Ultima reads align to the graph with the Ultima `minimap2.model`
   and are lifted to the linear reference. This uses the solo Ultima mapper's
   settings without the Illumina `--secondary=yes` override.
4. Joint DNAscope and PangenomeSV consume original Ultima (`LR:0`), lifted
   Ultima (`LR:2`), and ONT (`LR:1`). UltimaReadFilter is scoped to the original
   and derived Ultima RG IDs. ONT graph-update/SV jobs receive no Ultima filter.
5. Population annotation transfer and DNAModelApply use the joint model.
   Explicit indexing jobs finish the output contract.

Read extraction keeps the existing `tp,t0` auxiliary tags; minimap2 `-y`
preserves the FASTQ comment tags during realignment, as in the solo Ultima
pangenome path. Duplicate/secondary/supplementary reads are excluded from
extraction using the upstream `0xf00:0` mask. Ploidy estimation uses all supplied
Ultima alignments. Vendor model behavior with these inputs is still unvalidated.

## Outputs and receipts

For `ug_ont_pg.vcf.gz`:

| Output | Purpose |
|---|---|
| `ug_ont_pg.vcf.gz` + `.tbi` | Joint small variants |
| `ug_ont_pg_sv.vcf.gz` + `.tbi` | PangenomeSV calls |
| `ug_ont_pg_lift_deduped.cram` + `.crai` | Lifted Ultima reads; BAM + `.bai` with `--bam_format` |
| `ug_ont_pg_ploidy.json` | Ploidy/sex estimate |
| `ug_ont_pg_logs/` | Native command, run/task logs, process/job resource metrics |
| `ug_ont_pg_provenance.json` | Experimental profile, inputs, model roles, versions and outcome |

The aligned-input path preserves the upstream output name `lift_deduped`;
it does not run an additional duplicate-marking pass. The internal ONT
LongReadSV callset is an intermediate for graph updating; the final SV VCF
is from PangenomeSV. The upstream `--retain_tmpdir` option can preserve
intermediates when explicitly requested. Native resource metrics are retained;
the aligned-input path does not add FASTQ-only QC/MultiQC stages.

Receipt states are `validating`, `planning`/`running`, then `dry_run`,
`completed`, `failed`, or `interrupted`. Normal tool failures and handled
SIGINT/SIGTERM propagate as failure/interruption. A killed machine/process
may leave a nonterminal receipt; that is never completion evidence.
Completion requires nonempty outputs/indexes, readable ploidy JSON, native
logs/resource rows, and unchanged input/reference/bundle file identities.

Receipts retain absolute/resolved paths, byte sizes and modification times,
alignment-header/FAI hashes, model/bundle hashes, unchanged vendor metadata,
tool banners/executable hashes, CLI source hashes, read-group channels, and
log locations. Large alignment/reference files are identified by path/stat
and their inspected metadata, not full-file content hashes. This provenance
does not independently certify their biological identity or vendor origin.
`experimental=true`, `scientific_validation=pending`, and
`production_accepted=false` remain set even after functional completion.

## Validation state

Eight focused regression modules, including `tests/unit/test_ultima_pangenome.py`,
passed **218 cases** on the verified `ashg-etc` headnode on 2026-10-20. The exact
annotated fork tag `2.0.2` passed the same scope after wheel installation.
The controlling
[implementation ledger](plans/20261014_ultima_ont_hybrid_pangenome_ledger.md)
records the original approval holds, later explicit execution approvals,
exact commands and native evidence. Scientific runtime evaluation and
production acceptance remain pending.

Before scientific acceptance, freeze a same-donor Ultima/ONT pair, coverage,
truth set, regions, reference provenance, and compute budget. Compare with
matched existing Ultima+ONT hybrid and Ultima-only pangenome results. Record
SNP/indel precision/recall and stratifications, SV performance, model failures,
wall time, CPU and memory. An unsuitable joint model is an explicit evaluation
result requiring a suitable Ultima joint model, not silent substitution.
