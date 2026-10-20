# ashg-etc CLI and runtime evidence

Authority and exact infrastructure are recorded in the controlling CLI ledger.
All executable checks and builds in this workstream run on ashg-etc, as ubuntu.
No laptop container build, other-cluster execution, Ganon, Ganon2 or VEP.

## Runtime

- Root: `/fsx/work/pangenome_runtime/20261020`.
- Environment: `env`, created from the adjacent runtime_environment.yaml;
  actual exact conda packages and pip versions are frozen in native
  `evidence/conda-explicit-linux-64.txt` and `evidence/pip-freeze.txt`.
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
