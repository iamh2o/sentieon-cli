# Preparation collector 19.0.52 source asset

**PASS**, native qualification completed 2026-10-22 07:10:52 UTC. This stages
released source only. No collector or workflow ran.

`COLLECTOR_52=/fsx/work/pangenome_reporting/20261022/shared3030_collector_19.0.52`

The [receipt](asset_stage.receipt.json) binds the exact ashg-etc account,
generation, head and FSx. Root explicitly selected this already released
collector only for the new 30/30 preparation's two canonical snapshots:
three normal-AU sampling sources and one shared ONT preparation source.
Caller/preparation source 19.0.49 and caller collector 19.0.50 remain unchanged.
B owns collection, native source inventory and metric/attempt fidelity.

The parent directory existed and the exact destination was absent. The
original ubuntu runtime pane `pg_runtime_ashg_etc_20261020 @3/%3` was reused.
After a narrow review of the released public fetch contract, root approved:

```bash
git init -q /fsx/work/pangenome_reporting/20261022/shared3030_collector_19.0.52
day-clone --repository daylily-omics-analysis --git-tag 19.0.52 \
  --fetch-existing /fsx/work/pangenome_reporting/20261022/shared3030_collector_19.0.52
git -C /fsx/work/pangenome_reporting/20261022/shared3030_collector_19.0.52 \
  checkout --detach 026a976cd18c0711ea74e90ee45ced93168320e3
```

Public fetch uses the [configured repository](configured_repository.txt),
`git@github.com:lsmc-bio/daylily-omics-analysis.git`, with its declared
`aws_deploy_key` authentication. An origin remote is not required by
`--fetch-existing`; no origin was fabricated, and no hand fetch, seed commit,
local object substitution or alternate authentication was used. The native
public tool hash matches released DYEC 21.0.45:
`da7af8662afd041e51fa7df402b198415983504c1faef29cfd2c297baff57b46`.

The [fetch receipt](public_fetch.exit_codes) records public operator rc0/tee0.
The [annotated tag](fetched_tag.txt) is type `tag`, object
`7fe484db3aac8919afea09b44cf50be1563cf14b`, peeling to
`026a976cd18c0711ea74e90ee45ced93168320e3`. HEAD is detached at that commit
and [source status](source_status.txt) is empty. The wrapper and two helpers
match all three independently reviewed release hashes in
[actual_sources.sha256](actual_sources.sha256). The unchanged
[native transcript](stage.typescript) closed with [child rc0](stage.exit_code).

Transport is separate from the source-stage gate. The original idle SSM stream
had earlier closed to the local `jmajor` shell; Linux-only read checks failed
locally and no mutation occurred. Root authorized the same public
`dyec headnode connect` route. A separate [native ubuntu assertion](ubuntu_assert.tool.json)
and [target/pane preflight](native_target_pane_preflight.tool.json) preceded
staging. The initial closure is retained as an attributed continuation
observation, not invented verbatim raw evidence.

After all bytes transferred, reattachment returned an SSM broken pipe to the
local shell. The tmux pane had been detached, never terminated; its last
[closed capture](retained_pane.txt) remains evidence. Post-closure native state
was not rechecked, and no additional native mutation or reconnect followed.
[Transport observations](transport_observations.json) preserve both closures.

Thirteen closed native files, including inventory, total 24,966 bytes.
All twelve content hashes match the original [native inventory](SHA256SUMS)
and [local verification](local_content_hash_verification.txt). The retained
3,637-byte transport archive has SHA256
`09151a8e6e512bffd7570feb6b4550c38a14bc673b7cdf36176b5aedd1f850bb`,
matching the native digest. No analysis root, reads/models, pinned workflow
source, configuration, CLI code/wheel/tag or runtime environment changed.
