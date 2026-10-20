# Explicit vendor Ultima duplicate-marking receipt

`--sr_duplicate_marking_receipt PATH` is experimental-mode-only. It is an
explicit input for vendor-produced Ultima alignments that lack a Sentieon,
Picard or samtools duplicate-marking program record. Existing recognized
program evidence remains accepted without this flag. When supplied, the
receipt is always validated; a recognized program does not bypass its checks.

Top-level JSON fields:

| Field | Required value |
|---|---|
| `schema` | `sentieon.ultima_duplicate_marking.v1` |
| `status` | `completed` |
| `alignments` | One entry for every selected `--sr_aln`, with no repeated or unselected path |

Each alignment entry has these required fields:

| Field | Required content |
|---|---|
| `alignment` | Absolute `path`, positive integer `bytes`, `sha256`, `header_sha256` |
| `source` | Exact `s3_uri`, positive `bytes`, `header_sha256`, absolute `accepted_provenance_path`, `accepted_provenance_sha256`; optional existing accepted `sha256` |
| `vendor_program_ids` | All actual `@PG ID`s whose `PN` is `demux` or `sorter`; both program kinds and nonempty versions must occur |
| `state` | `marked` |
| `flags_preserved` | JSON `true` |
| `selected_flags_sha256`, `prepared_flags_sha256` | Equal lowercase SHA256 digests of the selected and independently decoded prepared record flag streams |
| `selected_read_groups`, `prepared_read_groups` | Equal maps covering every actual RG ID, each containing integer `primary_records` and `duplicate_primary_records` with `0 <= duplicates <= primary` |

The flag-stream format is UTF-8, in actual retained record order:
`QNAME + "\t" + RGID + "\t" + decimal_FLAG + "\n"`.
Primary means `FLAG & 0x900 == 0`. At least one primary record is required.
The producer audits the complete selected stream and independently decodes the
prepared CRAM. The consumer verifies the complete newly prepared alignment
SHA256, byte count and `samtools view --no-PG -H` header digest, and verifies
the accepted provenance file digest. It records source S3/size/header/existing
accepted SHA evidence without recalculating a parent-source full checksum.

Positive observed duplicate-primary count is required unless an explicit
`zero_duplicate_producer_receipt` supplies an absolute `path` and its `sha256`.
That bound native producer execution JSON must have `status=completed`,
`source={s3_uri,bytes,header_sha256}` equal to this entry, and an `argv` array
for `demux` with exactly one `--mark-duplicates=true` setting (the separate
`--mark-duplicates true` spelling is also accepted). Missing/default settings,
false values or conflicting settings cannot prove a zero-duplicate state.

Any explicit `--mark-duplicates=false` or `--mark-duplicates=0` in a vendor
header is rejected. No program record is fabricated and no duplicate flags
are changed by the CLI. Receipt and provenance file identities are frozen
through completion. The producer's independently decoded audit is recorded
as the record-audit authority; the consumer does not claim to repeat it.

Producer documentation: [Ultima UA/Demux/Sorter usage](https://github.com/Ultimagen/healthomics-workflows/blob/main/workflows/trim_align_sort/howto-ua-align-sort.md).
That vendor document explicitly describes UMI-aware duplicate marking with
demux and final CRAM creation by sorter. Actual HG002 headers identify five
demux/sorter 1.5.18 producer pairs; their omitted principal boolean is never
interpreted as an enabled default.
