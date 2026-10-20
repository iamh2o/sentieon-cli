# Closed accepted Ultima30x + ONT10x preflight

Public CLI `2.0.3 hybrid-pangenome --experimental_ultima --dry_run`
returned **0** in 76.23636722 seconds on ashg-etc, from
2026-10-20 20:47:43 to 20:48:59 UTC.
[preflight_receipt.json](preflight_receipt.json) records the operator invocation.
[HG002_provenance.json](HG002_provenance.json) is the native experimental
receipt: `status=dry_run`, `dry_run=true`, `experimental=true`,
`production_accepted=false`, HG002. It records the fixed joint model,
Ultima mapper, graph, haplotypes, reference and population assets.

The actual accepted UG and ONT headers and bounded indexed probes passed.
[reference_dictionary_checks.json](reference_dictionary_checks.json) records
all 195 ordered vendor SN/LN/M5 entries, HG002 sample identity, coordinate
sort, five ULTIMA read groups and one distinct ONT read group.
The public experimental CLI then performed its real-header/model/reference
validation and required typed duplicate-receipt verification, accepting
11,658,934 duplicate-primary observations. No PG or RG was fabricated.

[accepted_inputs.json](accepted_inputs.json) binds the input owner's COMPLETE
r02 preparation and byte-binding receipts, CRAIs, source identities and
duplicate-marking receipt. UG is 51,928,203,894 bytes, SHA256
`9c9ae740fa621836608edad6e7850bb1242e7e919052b65263cedd414afc66d2`,
depth `29.99891901105408943184300036`×.
ONT is 26,826,310,679 bytes, SHA256
`088a754d3e9bf4ead14d8627c974999a49f2f7fe796f095f0acb761ea7cce6ad`,
primary depth `9.999053238278962532309287144`×.
Both use all 195 full reference intervals; the owner separately proved
deterministic downsampling repeats. Owner digests were reused. Only the
native CLI's mandatory UG duplicate-receipt guard verified UG bytes again;
this closeout added no manual whole-input checksum pass.

The 32-argument [native_argv.json](native_argv.json) matches the released
DayOA 19.0.48 adapter projection, preserving accepted inputs, immutable
assets, PCR=false, 96 cores and kmer memory30. Only the direct public CLI,
explicit scratch output/log destinations and appended `--dry_run` differ
from the intended live invocation.
Argv SHA256:
`d83b7525f842e2471742bbf4e03807f598838d2c22562bda80ac4c575f762a71`.
Operator receipt SHA256:
`43bef7caea9140c8f205616a751d51030e81d36613b5407d24a37fd14a54a8fb`.
Native provenance SHA256:
`ace44ee88c8dd6e4ac2e75dad85f935b391095b87a9fa4be7d442c21c5ed80fe`.

Native stderr and provenance preserve the 184-HAPL-chain/195-GRCh38-path
heuristic warning and the unvalidated experimental joint-model warning.
The selected vendor pair's hashes remain in the parent asset receipt.
No warning was suppressed, no asset substituted, and no reference guard
bypassed. The inspection receipt's `pending` native fields describe its
earlier inspection stage; the closed invocation/native receipts above
supply the subsequent result.

Native source root:
`/fsx/work/pangenome_runtime/20261020/preflights/r02_ultima30x_ont10x`.
[evidence_inventory.json](evidence_inventory.json) binds 28 closed small
receipt/argv/log/header/read-visit files; it was transferred alongside them.
[local_transfer_verification.json](local_transfer_verification.json) verifies
native-to-local bytes/SHA256 for all 29 files, including that inventory.
Transport archive SHA256:
`e5949260865774de6620286a8be8032b8458f582866f2f41c9276612e071fe4e`.
No archive, operator helper, alignment, model, private signed URL or credential
is included here.

The seven expected calling products were absent after this dry run.
This proves bounded functional preflight in the isolated qualified CLI
environment; native caller-environment admission, variant calling,
scientific suitability and production acceptance remain separate.
The ordinary ILMN preflight's synthetic dry-run headers are documented in
the sibling evidence directory and are not attributed to this real-header
experimental validation.

The campaign root subsequently verified original whole-preparation SUCCESS
(controller=null, DayOA/Snakemake=0/0; actual foreground/dy-r/tee=0/0/0,
source5/input9 unchanged, no jobs), proof SHA256
`5c1befe8536fce830697e6809ff85940384c2323792345d1015439296aac3758`.
The root retains that independent proof. Combined preparation benchmark
collection rc2 remains a separate reporting-layout blocker, without
alternate partial-cost acceptance. Root's proven-source promotion and
future catalog/configure/caller/scientific gates remain separate.

This evidence-only closeout ran no additional preflight, test, build,
install or model download. CLI2.0.3 tag/code/wheel are unchanged.
