# ashg-etc CLI and runtime evidence

Authority and exact infrastructure are recorded in the controlling CLI ledger.
All executable checks and builds in this workstream run on ashg-etc, as ubuntu.
No laptop container build, other-cluster execution, Ganon, Ganon2 or VEP.

## Runtime

- Root: `/fsx/work/pangenome_runtime/20261020`.
- Environment: `env`, created from the adjacent runtime_environment.yaml;
  actual exact conda packages and pip versions are frozen in native
  `evidence/conda-explicit-linux-64.txt` and `evidence/pip-freeze.txt`.
- This isolated CLI environment is not a solve or admission receipt for
  DayOA `hybrid_pangenome_v0.2.yaml`. Native rule-environment admission remains
  separate. Official vg/KMC binaries have explicit `env/bin` links; the existing
  Sentieon driver must use its original absolute path/bin directory because its
  shell wrapper cannot be relocated through an environment symlink.
- Observed: samtools 1.22.1 / HTSlib 1.24, bcftools 1.22 / HTSlib 1.24,
  mosdepth 0.3.14, vg 1.73.0, Sentieon 202503.04, KMC 3.2.4-pipe2.
- vg and KMC source URL/SHA256 match the existing repository Dockerfile;
  no container build was performed. Native download archives remain retained.
- Existing immutable driver and Ultima1.3 mapping bundle are read from
  `/fsx/references/runtime_assets/cached_envs/sentieon-genomics-202503.04/`.
- Reference remains the explicit vendor `panhg38/hg38_ucsc.fa`; no substitution.

## Focused checks

Executed inside `pg_runtime_ashg_etc_20261020`, retained ubuntu interactive tmux:

```bash
python -m pytest \
  tests/unit/test_ultima_pangenome.py \
  tests/unit/test_hybrid_pangenome.py \
  tests/unit/test_hybrid_vcf.py \
  tests/unit/test_dnascope_hybrid_components.py \
  tests/unit/test_fork_hybrid_stage1.py \
  tests/unit/test_cli_args.py \
  tests/unit/test_pipeline_lifecycle.py \
  tests/unit/test_kmc_patch.py -q --tb=short
```

Initial result: three collection errors, `ModuleNotFoundError: tests.utils`,
recorded in native `evidence/focused_cli_tests_initial.log`. Added explicit
`tests/__init__.py` and `tests/utils/__init__.py` to make repository helper
imports unambiguous. Repeated exact scope: **216 passed in 6.24s**, native
`evidence/focused_cli_tests_after_import_fix.log`.

These cases exercise routing, invalid options/assets/headers, preserved fork
components and checkpoint behavior, receipts, interruption and lifecycle.
They are synthetic functional checks; they establish no HG002 calling accuracy.

## Native asset preflight correction

Release 2.0.1's strict Ultima guard rejected the actual vendor v2.1 pair:
GRCh38 backbone paths = 195, HAPL top-level snarl chains = 184, HAPL k = 29.
Top-level chains describe the graph's snarl decomposition; they are not
reference paths. The existing shared base had already treated count mismatch
as a warning; the experimental adapter incorrectly elevated it to failure.
See [vg's chain model](https://github.com/vgteam/vg/wiki/Snarls-and-chains).

Release 2.0.2 keeps k=29 and populated HAPL structural checks, rejects a changed
GBZ/HAPL pair using exact observed content hashes, and records both hashes.
New regression cases accept the observed 184-chain index and reject a changed
pair. Eight-module candidate result: **218 passed in 6.58s**. Initial failed
native qualification remains `evidence/qualify_assets.log`; corrected metadata
and bundle-member checks pass in `evidence/qualify_assets_v2.log`, producing
native `evidence/asset_ready.json`. Hash authority remains the observed vendor
download pair; this does not claim a vendor-signed checksum manifest.

## Asset publication

The three exact assets and their immutable destination keys are encoded in
`stage_assets.py`. Reads/downloads occur on ashg-etc. Initial native S3
CreateMultipartUpload failed with AccessDenied because the headnode role has
no s3:PutObject permission to the shared reference bucket. No object was written.
A manual probe likewise failed at CreateMultipartUpload; its supplied metadata
digest was not the measured digest and is not evidence. Actual measured joint
bundle digest is `de2114917bef8f78164b73bee35113f3f8a399f781709376d9bed05301936f79`.

Root expressly approved operator-signed multipart upload with bytes retained
on ashg-etc and no IAM changes. Signed URLs must never enter repository logs,
evidence, or tool output. Transfer receipts retain observed source metadata,
bytes/SHA256, exact destination, S3 version/ETag and verification results.
Native `evidence/stage_assets.log` retains the first failure; do not overwrite.

All three uploads completed and exact object bytes, SHA metadata, ETags and
version IDs were independently read back; see `asset_publication_receipts.json`.
Local staged asset qualification is retained in `asset_ready.json`.

## Reference and duplicate-state qualification

`compare_graph_reference.py` records the actual extraction command, precise
`GRCh38#0#` comparison-name mapping, 195 reference sequence lengths/M5 values,
and comparisons to both candidate FASTAs and accepted source headers. All 195
graph backbone sequences match vendor `hg38_ucsc.fa`; the standard Bjuice/source
reference matches 181 before ambiguity normalization. The inputs workstream
proved the remaining differences are 94 IUPAC-to-N substitutions with no ACGT
changes, lengths or indels, and full per-contig normalized sequence identity.
That workstream owns explicit source-reference decode and target MD/NM refresh.
No reference file, graph or vendor bundle was modified.

The existing `panhg38/hg38_canonical.bed` has 24 rows for chr1-22/X/Y with exact
FAI bounds, covering 3,088,269,832 bases. It excludes 171 contigs total, including
chrM. SHA256: `783b97a5ea77e54531ffdb98b8fda6234c5e22b11b3101f0021d71b77d160dba`.

Release 2.0.3 adds the explicitly approved typed vendor duplicate receipt;
see `duplicate_marking_receipt_contract.md`. It preserves existing known-PG
acceptance while rejecting inferred native defaults, fabricated PG records,
source/provenance/header/byte mismatches and changed flag/count evidence.
The focused command above adds `tests/unit/test_ultima_duplicate_marking.py`:
nine-module final candidate result **232 passed in 17.91s**, native
`evidence/focused_cli_tests_duplicate_receipt_final_candidate.log`, rc0.
Intermediate candidate transfer errors were confined to the scratch candidate,
preserved in the prior failed logs, and corrected by verifying all transferred
source hashes before that successful repeat. No biological job consumed them.

The exact annotated `2.0.3` clone then built and installed its wheel and passed
the same 232 cases in 50.19s. Runtime qualification, actual binary version/hash
checks and patched-KMC stdin probe all returned rc0. See `env_ready-2.0.3.json`
and `test_receipt-2.0.3.json`. Native source `cli-2.0.3` remained clean.

Release commit: `1358db44816e01d20f32856eebbc496d45638060`.
Annotated tag object: `8a718ece11dc39017fc1fe8275573e4c7bbab90c`.
Wheel SHA256: `09c0616ecafae37d4ae03abb8700c7d3eda695b13fb2d728a4ca37e61e968517`.
Biological execution and scientific results remain campaign-root work.
