# Actual admitted sampler environment qualification

**PASS**, 2026-10-22 05:33:23 UTC. This closes the sampler-environment gate
left pending in the earlier asset receipt. It does not accept prepared inputs
or establish workflow completion. No input/file audit was executed here.

Native prefix:
`/fsx/resources/environments/conda/ubuntu/ashg-etc-d1e05a50-cc74-11f1-9b2e-0afff600b0d9/4e0169e1453c1de1f7186c1bbd9f85c9_`.

| Executable | Observed version |
|---|---|
| Prefix `bin/seqkit` | 2.14.0 |
| Prefix `bin/pigz` | 2.8 |
| Prefix `bin/igzip` | 2.31.0 |
| `/usr/bin/gzip` | 1.10 |
| `/usr/bin/cmp` | GNU diffutils 3.8 |
| `/usr/bin/sed` | GNU sed 4.8 |
| `/usr/bin/mkfifo` | GNU coreutils 8.32 |
| `/usr/bin/awk` → `/usr/bin/gawk` | GNU Awk 5.1.0, API 3.0 |

The [receipt](sampler_environment_qualification.json) and unchanged
[native transcript](sampler.typescript) record version/help calls only.
Seqkit `seq` supports `--name`, `--only-id`, `--threads`; `stats` supports
`--all`, `--tabular`, `--threads`. Igzip supports decompress/stdout; gzip
documents integrity testing. Complete help files are retained. The receipt's
ID-regexp string retains the help's escaped rendering of its default; no
ID-regexp override or audit command was executed. Actual selected conda
versions/builds/channels are in [package metadata](sampler.packages.json),
including seqkit 2.14.0 despite its unpinned declaration in the immutable YAML.

The required [read visit](analysis_read_visit.json) preceded all analysis-root
reads at 05:32:33.748839 UTC. Its metadata reports user `unknown`; the separate
live POSIX check returned `ubuntu`, on exact head `i-004609f020b02705a`.
The foreign workflow write lock was neither acquired nor changed. Reads were
limited to the handed source YAML, runtime config, jobscript and a bounded
controller-log excerpt; snapshots are evidence and must not be executed.

Source HEAD was clean at DayOA 19.0.49 /
`1319db5785b8ba371592ba082716cfc3ae63d112`. The native YAML hash
`cbe09afb335f957effdafe2672d2bd5e64a014e006cdb1fb9265813356583344` matches
the annotated release's exact file. Runtime config remains
`bd9b7679fbeea00824a8e9a8a2653e2096eaaa4cc0429a28d26528bed56b68a1`.
The handed native [jobscript](native.sampler_jobscript.sh), hash
`1275a83875cae53dc5d00c361e4468c38b4e3f282328fd0e85eaea02e0e271ba`, binds
the same environment prefix and in-clone config. The
[controller excerpt](native.env_admission_excerpt.txt), original lines 698/700,
directly records creation of `sent_pangenome_v0.2.yaml` at that prefix.
There is no invented standalone environment-admission report.

This is the paired-sampler environment. Its older CLI/vg declarations remain
unchanged; it does not replace the separately qualified CLI 2.0.3 hybrid caller
runtime. B owns prepared-input completion and audits; C/B own all workflows.
No installation, source/config edit, test/import campaign, payload hash,
prepared-data read, audit, workflow dispatch or job administration occurred.

Thirteen closed native files total 48,088 bytes. Every content file matches
the native [SHA256 inventory](SHA256SUMS). The 12,840-byte transport archive
has SHA256 `3d47e313c2cc64b74ae276daa54716dae500395208bdf125ece2d1f8b7b75d26`;
native/local archive and content hashes matched. Receipt SHA256 is
`2fc64f8be7d92271aa75c23fe3aa62d092b0fd399206755b2acc2b54fa02c6fd`.
The native script closed rc0; raw evidence bytes are unchanged.

B additionally requested the AWK executable/version for the frozen audit
counter. At 05:38:33 UTC, `/usr/bin/awk` resolved to `/usr/bin/gawk`, whose
version-only command closed rc0. Its [path](awk.path.txt),
[version transcript](awk.version.typescript) and [native inventory](awk.SHA256SUMS)
are a separate three-file, 1,262-byte supplement. Local content hashes match
the original inventory's native absolute paths. The 936-byte transport archive
SHA256 is `abed2a4522a3de9f05f839dc06f769887524960b47bfc29430f5aca52c55b366`.
No counter or audit was executed.
