# 30× + 30× bounded runtime qualification

At 2026-10-22 05:14:57 UTC, the existing CLI/driver and immutable asset
**small metadata** qualification passed on the approved ashg-etc headnode.
The actual admitted paired-sampler environment/version remains pending B's
native admission handoff. This receipt does not qualify prepared reads or
dispatch a workflow.

Root's second direct execution approval is recorded as
`3030_runtime_approval_20261022T044825Z`. Target: account `108782052779`,
region `us-west-2`, ashg-etc generation
`d1e05a50-cc74-11f1-9b2e-0afff600b0d9`, head `i-004609f020b02705a`,
FSx `fs-0d55fedaeb3ca246b`. The public DYEC 21.0.45 connection independently
confirmed ubuntu/head identity and the Lustre mount; C's
[closed readiness proof](https://github.com/lsmc-bio/daylily-ephemeral-cluster/blob/32138e1edc90a1f3e02406e8827cc7dee2c3b93f/docs/plans/20261020T124250Z_pangenome_catalog_ilmn_execution/execution_30x30x_20261022T045210Z/readiness.cluster.json)
binds the generation and head, with its adjacent mounts receipt binding FSx.
Inspection used the retained, idle, single-pane runtime session
`pg_runtime_ashg_etc_20261020`, pane `%3`/PID 39374. No analysis root was read.

The [native receipt](asset_runtime_qualification.json) records fresh CLI 2.0.3,
driver 202503.04, clean native CLI commit
`1358db44816e01d20f32856eebbc496d45638060` and annotated tag type. The existing
asset/env receipts match the previously frozen local hashes. The native
environment receipt is `evidence/env_ready.json`; its archived local filename
is `env_ready-2.0.3.json`.

Fresh archive catalogs/vendor JSON confirm the existing joint hybrid bundle
1.0 and Ultima mapper 1.3 roles. Their vendor metadata was preserved, including
the mapper bundle's older graph/population declarations. FAI is 195 contigs /
3,099,922,541 bases; calling BED is 24 contigs / 3,088,269,832 bases, excluding
171 contigs total including chrM. Population ID is
`population-hprc-v2.0-20260528`. GBZ magic/size and HAPL version 5, k=29 and
184 chains agree with the frozen profile. The 184-chain/195-path distinction
remains recorded. Only 436-byte LongReadSV and 590-byte mapper members, small
receipts, FAI and BED were freshly hashed. Large asset/read payload digests
were reused; no new full-payload hash campaign or graph extraction occurred.

Two operator inspection mistakes are retained as actual rc1 evidence:

1. [Initial log](assets.typescript): unsupported `sentieon --version`;
   the documented `sentieon driver --version` then passed.
2. [Second log](assets.corrected.typescript): the local archival env-receipt
   filename was used on the native host. The exact producer source writes
   `env_ready.json`; that native file subsequently matched the frozen digest.

The [final metadata log](assets.final.typescript) closed with child rc0 and
the explicit PASS marker. Neither earlier failure was recast as zero or as an
asset/runtime failure. No source/config/model change, install, test/import
campaign, biological call, analysis-root write, lock acquisition or export
occurred.

Five closed native files total 19,484 bytes. Their
[SHA256 inventory](SHA256SUMS) verifies all four content files. The retained
transport archive is 5,105 bytes, SHA256
`b92b8cff519e0ce1f17288c424b66c42b953fc357d21e89faf12ba3c7a0653c0`;
native/local archive hashes and all content hashes matched. Raw terminal bytes
are preserved unchanged.

The independently reviewed DayOA 19.0.49 resolver consumes manifest rows only
(`analysis_input_resolver.py` lines 193–208). Its derived canonical identity
(532–562) uses sample/specimen, source AU label, ordered input UID/ordinal/
provenance/library and declared dataset ID/URI/SHA. Runtime identity
(587–645, 675–730) uses the supplied external sample and canonical digest for
these blank-EUID rows. Capsule root/CWD/report destinations do not enter.
Thus the metadata capsule's native AU report can bind a separate preparation
capsule with byte-identical six tables; matching native six-table hashes and
the actual preparation config/dry proof remain required. No private resolver
was imported or invoked, and no native AU identifier was calculated here.

Next: inspect the actual admitted `sent_pangenome_v0.2.yaml` prefix and seqkit
version once B supplies native solve/jobscript provenance. ILMN seed remains
the released explicit 7; ONT independently retains seed 20261020. Callers/prep
remain DayOA 19.0.49, external collector 19.0.50, CLI 2.0.3. Scientific
suitability and customer acceptance remain unassessed.
