# Ultima30x + ONT10x native core and QC PASS — 21 October 2026

The approved ashg-etc experimental `huomr2p` run has completed native calling
and alignment QC. The closed 12:08 snapshot below predates final packaging.
Root later reported package/artifact acceptance PASS and foreground 6/6 SUCCESS/
return0 at 12:16:54 UTC, with source 1319db unchanged after return.
The owner's later 12:19:58 UTC public observation records the original attempt
SUCCESS/completed 12:17:13Z, canonical 0/0/0, inactive controller, no exact-root
jobs and write lock unlocked/owner null. Observation SHA256 supplied by root:
`dd54171d30f6dcbdc7e47a37de119ba185c6effbe31525637bdbdcf159a6f4c5`.
Independent closed bytes/sealed transcript+ten-invariant proof remain pending;
the post-success collector is held. This closeout independently verifies
core/QC only; the later whole milestone is attributed to the owner. Cross-platform
accuracy, scientific suitability and production/customer acceptance remain
unestablished.

Analysis: `hg002-huomr2p-30x10x-20261020-r01`.
Native AU: `HG002-wdth3tk3gpbvjt`; biological sample: HG002.
Native attempt: `11471349-d4f5-4027-9d70-31cc5a07afe6`.
Pins: DayOA 19.0.49, DYEC 21.0.45, iamh2o/sentieon-cli 2.0.3; driver 202503.04.
The native analysis root is
`/fsx/analysis_results/ashg-etc/hg002-huomr2p-30x10x-20261020-r01`.

| Gate | Closed evidence |
|---|---|
| Caller core | PASS, outcome called, source return0 |
| Joint model application | DNAModelApply completed 11:42:15.647 UTC in 47.65s |
| Native CLI | Completed 11:42:37.806801 UTC; dry_run=false |
| Core workflow rule | Finished 11:42:48 UTC |
| Alignment QC | Terminal PASS/return0/MEASUREMENTS_COMPLETE, generated 12:06:38 UTC |
| Quality disposition | Execution PASS, QC PASS, scientific NOT_ASSESSED, customer_release_eligible=false |
| Packaging/whole workflow | At 12:08:07.985118 UTC, Slurm 12 RUNNING; all workflow return codes null |

[core.component.native.json](core.component.native.json) declares 14 nonempty
artifact roles, including small-variant VCF/index, PangenomeSV VCF/index,
ploidy, lifted alignment/index, original Ultima and ONT inputs/indexes,
duplicate evidence, command manifest and native provenance.
[core_completed_proof01.native.json](core_completed_proof01.native.json)
independently records nine generated-role metadata matches and the actual
DNAModelApply completion/DAG-finalization log lines.
Large alignment/VCF bytes were not read or rehashed by this closeout.

[native_provenance.native.json](native_provenance.native.json) records
`status=completed`, `experimental=true`, `production_accepted=false` and
scientific validation pending. The unchanged model composition is
`HybridPangenomeIlluminaONT1.0.bundle/dnascope.model` plus the released
Ultima 1.3 pangenome mapper. Successful model application demonstrates this
run executed; it does not validate that cross-platform composition's accuracy.
The 184-HAPL-chain/195-reference-path heuristic warning and the experimental
model warning remain preserved.

[quality.native.json](quality.native.json) retains original metric floats and
the exact decimal mean-depth strings below; no value was recomputed.

| Alignment role | Mean depth over 3,099,922,541 reference bases |
|---|---|
| Original Ultima SR | 29.99891901105408943184300036 |
| Lifted SR | 4.325412616172850365424663042 |
| ONT primary-only | 9.999053238278962532309287144 |

Every role retains 195 full-length interval checks. Combined depth uses
**original SR + ONT only**; lifted SR is repeated sequence and is not added.
The recorded combined-depth metric is 39.99797224933305. Original SR depth,
ONT primary depth, combined depth and ONT QNAME-union mean aligned length
all pass their explicit thresholds. The QNAME-union length metric is
6729.276501218836 bp, with threshold 1000. These QC checks contain no truth-set
precision/recall or scientific-acceptance result.

The receipts distinguish runtime qualification from declarations. Native
provenance captures actual samtools/bcftools 1.24 in the hashed DayOA rule
environment, alongside the explicit CLI environment. Existing tool-version
capture invokes unsupported `vg --version` and records rc1; VG 1.73.0 remains
declared and previously qualified. This reporting limitation is preserved,
with no fabricated successful probe or new runtime action. Core metadata
also explicitly records `native_metrics_state=not_emitted_for_aligned_short_reads`;
the model-application resource/log evidence is retained separately.

Both closed inventories and all eight listed native receipt files were
independently byte/SHA verified before copying. Core inventory SHA256:
`be453046122404787e23da61d15aa78d7cb46241b419b2fd5e79e4c0ae593b92`;
QC inventory SHA256:
`ea21d037d64625d1eb7ab9088d0c1d5e3fdbb82867039fec3e459349bd33ebd6`.
The ten copied files total 197,300 bytes including their inventories.
[core_qc_closeout_verification.json](core_qc_closeout_verification.json)
records source/local byte equality, receipt consistency, scope and limitations.
`evidence_inventory.json` binds this local evidence directory.

Source: the campaign root's closed local DayOA evidence directory
`docs/plans/20261020T094136Z_hiomr2p_huomr2p_bjuice20_multiagent/execution/huomr2p_execution_20261021/`.
The core bundle originated in root's evidence commit a8d0652c; root now reports
07b15bb6 published. Root owns later package/workflow receipt closeout. No cluster/headnode/S3 query was
performed here. The 12:08 snapshot is historical, not a fresh packaging status.

Root's later package/artifact acceptance PASS handoff identifies closed inventory
prefix 37483d41 (five files/567,678 bytes); those additional files were not read or
copied here. The canonical whole milestone is now owner-verified; independent sealed
terminal/transcript/invariant transfer remains pending. An earlier read-only
helper precondition rejected state/controller invariants before snapshot and
made no proof/analysis/benchmark writes; that rejection is retained, never
reinterpreted as zero. The public optional canonical-artifact warning also
remains; the exact clone-v2 receipt establishes 0/0/0. Other-arm acceptance, scientific
evaluation and export/delivery remain separately owned. PG-032
combined preparation benchmark collection stays BLOCKED/rc2 with no alternate
cost acceptance. The separate linear Ultima+ONT owner ledger remains
unlaunched; this run does not establish its completion.

Only CLI docs/evidence changed. CLI 2.0.3 code, numeric annotated tag, wheel,
vendor models and references remain unchanged. No test/build/install,
biological rerun, new full input/output hash, Google Doc edit or DayOA/DYEC
source edit occurred in this closeout.
