# Closed ILMN 2x150 + accepted ONT preflight

On ashg-etc, public CLI `2.0.3 --dry_run` returned **0** in 1.793724 seconds at
2026-10-20 18:35 UTC. [preflight_receipt.json](preflight_receipt.json) is an
operator invocation receipt, with exact argv, native stdout/stderr and separate
accepted-input evidence. It is not a native experimental-profile receipt.
Ordinary CLI dry-run alignment RGs are synthetic. Real ONT header/index/sample/
RG checks are separately recorded in
[reference_dictionary_checks.json](reference_dictionary_checks.json): all 195
ordered vendor reference SN/LN/M5 entries, HG002/ONT and coordinate sort match.
The single bounded indexed probe returned rc0. Native population validation
reported agreement on all 195 graph-reference contig lengths.

[accepted_inputs.json](accepted_inputs.json) binds the completed r02 ONT
producer receipt, its CRAI/source identity and the accepted 2x150 FASTQ paths.
The prepared ONT is 26,826,310,679 bytes, with sole-owner final SHA256
`088a754d3e9bf4ead14d8627c974999a49f2f7fe796f095f0acb761ea7cce6ad`;
this preflight reused it without another whole-file checksum pass. Its primary
depth is `9.999053238278962532309287144` across 195 full reference intervals,
including explicit zero evidence for 32 no-record query contigs. No UG/partial
input was read. No calling products were created; no scientific suitability or
production/caller-environment acceptance is established.

The exact 31-argument [native_argv.json](native_argv.json) matches the frozen
DayOA 19.0.48 adapter specification, retaining selected inputs, assets, RG,
PCR=false, 96 cores and kmer memory30. Only authorized scratch destinations,
public CLI argv0 and `--dry_run` differ from the intended live invocation.
Argv SHA256: `2b7a71df76b59b4d212b4a05defd57ef24bff96f575ddd53afa2a450a6115ad8`.
Preflight receipt SHA256:
`4a7da868ba87cee01f69a04b8d5a20a564735c711bd88c91a5c3d5c397dfdd5c`.

Native stderr preserves the existing warning that the selected HAPL has 184
top-level chains while the graph has 195 GRCh38 paths. The selected vendor
pair's observed hashes/qualification are separately frozen in the parent
`asset_ready.json`; this heuristic warning was not suppressed or bypassed.

Native source root:
`/fsx/work/pangenome_runtime/20261020/preflights/r02_ilmn150_ont10x`.
[closed_transfer_inventory.json](closed_transfer_inventory.json) binds 25 closed
receipt/argv/log/header/read-visit files. The inventory itself was transported
with them. [local_transfer_verification.json](local_transfer_verification.json)
records native-to-local byte count/SHA256 equality for every selected file.
Transport archive SHA256:
`b47a43096d194db6bf5e6ee0a9ad4625b91e5c4abf799e7724cdf542e5b03d20`.
No archive, source helper, alignment, model, private signed URL or credential
was added to this evidence directory. This closeout ran no additional preflight,
test, build, install or input checksum pass; the immutable 2.0.3 tag/code/wheel
remain unchanged. UG/whole-live/full caller/scientific gates remain pending.
