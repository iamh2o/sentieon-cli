# HG003 5x gVCF, DayOA hardcut, and vcfeval validation ledger

Created: 2026-08-01T10:16:12Z
Owner: Codex (`codex-sentieon-cli-171i-20260801`)
Branch: `codex/hg003-gvcf-hardcut-validation-1.7.1i`
Analysis root: `/fsx/analysis_results/preval-hiomr2/sentieon-cli-hybrid-core-runtime-1.7.1i-hg003-5x`

## Objective

Run the same frozen HG003 5x Illumina plus 5x ONT aligned inputs through the
untouched Sentieon CLI `v1.7.0` source and released accelerated fork `1.7.1i`
in native `--gvcf` mode. Prove or reject exact semantic parity, derive a hard
VCF from each gVCF using the DayOA hardcut command, compare GIAB HG003 v4.2.1
RTG `vcfeval` results, and separately document the distinction between the
gVCF-derived hard VCF and the CLI's directly emitted native hard VCF.

The four artifact classes remain distinct throughout:

1. CLI native gVCF (`dnascope-hybrid --gvcf`)
2. DayOA hardcut derived from that gVCF (`GVCFtyper --emit_mode variant`)
3. CLI native hard VCF (`dnascope-hybrid` without `--gvcf`)
4. RTG `vcfeval` output for one specific hard-VCF candidate

## Frozen contracts

- Original CLI: upstream tag `v1.7.0`, commit
  `1bf377d3ce79fc4d8c2dc221e1f696441e38349d`.
- Accelerated CLI: annotated fork tag `1.7.1i`, commit
  `e4f0ff8bf4ddd882cb154774178d2b40babba056`, package version `1.7.1+i`.
- Sentieon Genomics: `202503.03`.
- DayOA hardcut source: annotated tag `13.0.116`, commit
  `7b5e8f7c8df82de2b7478bec7ceadb08430950ad`.
- Analysis unit: `HG003-5X-CLI-RUNTIME`.
- Short-read input:
  `prepared/HG003-5X-CLI-RUNTIME.sr.prepared.cram` plus CRAI.
- Long-read input:
  `prepared/HG003-5X-CLI-RUNTIME.lr.aligned.cram` plus CRAI.
- Reference: GRCh38 no-alt analysis set.
- Scope: `inputs/full-primary.bed`, SHA-256
  `6f6179a3bc159e9527a56e665f8e5363fb8ee4af58696fbbdd043d1e0df6128d`.
- Model: `HybridIlluminaONT2.0.bundle`.
- dbSNP: `Homo_sapiens_assembly38.dbsnp138.vcf.gz`.
- Population VCF: `pop-v20g41-20251216.vcf.gz`.
- GIAB truth: HG003 small variants v4.2.1 `giabHC` VCF and BED.
- RTG template:
  `hg38/rtg/Homo_sapiens_assembly38.fasta.sdf`.
- Slurm contract: `sbatch --partition i128nvme --comment RnD
  --cpus-per-task=128`.
- Excluded work: raw-FASTQ preparation, QC, MultiQC, mosdepth, SV, CNV,
  scheduler pending time, and cluster administration.

## DayOA `13.0.116` hardcut command contract

The checked-in `sentdhiomr2_inflection_vcf_compat` rule calls
`workflow/scripts/hiomr2_faithful_hybrid.py hard-vcf`. Its material commands
are frozen here without changing their arguments or order:

```text
sentieon driver \
  --reference REF \
  --thread_count THREADS \
  --temp_dir TMP \
  --algo GVCFtyper \
  -d DBSNP \
  --vcf INPUT.g.vcf.gz \
  --emit_mode variant \
  hard.raw.vcf.gz

bcftools sort \
  --temp-dir TMP/bcftools-sort \
  -Oz -o OUTPUT.vcf.gz hard.raw.vcf.gz

bcftools index --threads THREADS --tbi --force \
  --output OUTPUT.vcf.gz.tbi OUTPUT.vcf.gz
```

## Control ledger

| ID | Area | Requirement | Status | Category | Approval Gate | Owner | Evidence | Root Cause | Terminal Note |
|---|---|---|---|---|---|---|---|---|---|
| SEARCH-001 | Existing evidence | Search dedicated CLI roots and available Take11-through-Take71 roots before submitting new compute | SUCCESS | investigation | 0 | Codex | Read visits and artifact inventory: extant roots in the requested historical interval were Take17, 20, 21, 25, 30, 41, 48, 49, and 61; Take48 contains an HG003 CLI-1.7.0 gVCF/workflow hardcut; Take49 and the dedicated `cli-gvcf-hardcut-vcfeval-20260730T130315Z` root contain completed three-way evidence; Take61/Take71 environments remain CLI 1.7.0 | The exact `1.7.1i` tag was created on August 1, after the relevant Take runs | Existing data is reused for the upstream semantic issue; no historical artifact was misclassified as exact release-tag proof |
| EXIST-001 | Existing three-way result | Validate the reusable HG003 5x/5x raw-gVCF, GVCFtyper-hard, native-hard, direct comparison, and RTG evidence | SUCCESS | validation | 0 | Codex | Jobs 1170-1174 and 1188 completed; raw gVCF and GVCFtyper hard have byte-identical RTG summaries (SHA-256 `74c800d876398824ea989cb5278e79b4c86f2f48826224fc64da6e9cbf6a28e2`); native hard differs; exact commands and metrics retained in the dedicated ledger | N/A | Sufficient to file the construction-path issue without rerunning that analysis |
| INV-001 | Inventory | Verify clean exact-tag CLI checkouts, frozen inputs, truth data, tools, scheduler contract, and output-name non-collision | SUCCESS | validation | 0 | Codex | Detached exact-SHA worktrees under `checkouts/official170` and `checkouts/release171i`; annotated release tag verified; frozen CRAMs, scope checksum, tools, DayOA `13.0.116`, truth/SDF, prior native-hard results, and empty publication paths verified | N/A | Fail-hard payload preflights repeat the critical checks on compute |
| GVCF-001 | Original lane | Run upstream Sentieon CLI `v1.7.0 --gvcf` on the frozen prepared CRAMs | IN_PROGRESS | execution | 1 | Codex | Job `2606` ran for `03:00:58` and completed the CLI/VCF conversion, but exited `2:0` at the post-run `indexed_record_count` gate; initial job `2598` failed before CLI execution | The initial payload derived a helper path from Slurm's copied `BASH_SOURCE`. Job 2606 then exposed that Sentieon's queryable emitted TBI reports zero htslib record-count statistics. | No result was published. The corrected payload now force-rebuilds the TBI with the pinned bcftools before checking `--nrecords`; replacement job pending approved scheduler action. |
| GVCF-002 | Accelerated lane | Run released fork `1.7.1i --gvcf` on exactly the same prepared CRAMs and arguments | IN_PROGRESS | execution | 1 | Codex | Job `2611` ran for `01:58:13` and completed the CLI/VCF conversion, but exited `2:0` at the same post-run `indexed_record_count` gate; initial jobs `2599` and `2607` failed before CLI execution | Jobs 2599 and 2607 were preflight failures described above. Job 2611 independently confirmed that Sentieon's queryable emitted TBI reports zero htslib record-count statistics. | No result was published. The same corrected TBI-rebuild gate will be used; replacement job pending approved scheduler action. |
| SEM-001 | gVCF parity | Require exact record-body, semantic-header, sample/contig order, representative tabix-query, BGZF, and tabix parity | OPEN | acceptance | 2 | Codex | Pending comparison output | N/A | Pending |
| HARDCUT-001 | DayOA hardcut | Derive one hard VCF from each gVCF using the exact DayOA `13.0.116` GVCFtyper, sort, and index commands | OPEN | execution | 2 | Codex | Jobs `2600`, `2608`, and `2612` are all pending with `DependencyNeverSatisfied`; their exact dependencies are recorded below | Each job used `afterok`, and at least one direct parent in every dependency set failed. | The three jobs cannot be released into runnable state. Cancellation and one corrected replacement dependency chain await the required explicit post-proposal scheduler approval. |
| SEM-002 | Hardcut parity | Require exact record-body and semantic-header parity between the two gVCF-derived hard VCFs | OPEN | acceptance | 3 | Codex | Pending comparison output | N/A | Pending |
| RTG-001 | Derived vcfeval | Run RTG vcfeval against HG003 GIAB v4.2.1 and require identical summaries and category VCF bodies for the two derived hard VCFs | OPEN | acceptance | 3 | Codex | Pending RTG output | N/A | Pending |
| MODE-001 | Construction paths | Compare upstream native hard mode against its gVCF-derived hardcut, quantify semantic differences, and compare their RTG summaries | OPEN | investigation | 3 | Codex | Pending mode-distinction report | N/A | Pending |
| MODE-002 | Released construction paths | Compare the retained-normalizer native hard result against the released gVCF-derived hardcut, with code-equivalence proof from commit `501b57d` to the release tag | OPEN | investigation | 3 | Codex | Pending mode-distinction report | N/A | Pending |
| PR-001 | Upstream PR | Add exact commands, run IDs, semantic hashes, timings, and RTG findings to Sentieon PR 28 | IN_PROGRESS | publication | 4 | Codex | Existing CLI-1.7.0 semantic evidence added at `https://github.com/Sentieon/sentieon-cli/pull/28#issuecomment-5151049963`; exact release-tag A/B results remain pending | N/A | Existing and release-tag evidence are kept explicitly separate |
| ISSUE-001 | Sentieon issue | Open an upstream issue that clearly distinguishes raw-gVCF/GVCFtyper-hard vcfeval equivalence from native-hard divergence | SUCCESS | publication | 4 | Codex | `https://github.com/Sentieon/sentieon-cli/issues/29` | GitHub App lacked upstream issue-write permission, so the authenticated `gh` fallback was used | Filed from completed existing data; no new compute was needed for the issue |
| CLOSE-001 | Closeout | Make every ledger row terminal and report remaining gaps without weakening a failed gate | OPEN | closeout | 5 | Codex | This ledger | N/A | Pending |

## Acceptance rules

- No output is published from a failed or incomplete CLI run.
- Compression bytes and volatile command/date/scratch-path header lines may
  differ; decompressed record bodies may not differ in matched implementations.
- Semantic headers include `FILTER`, `INFO`, `FORMAT`, `contig`, `reference`,
  and the final sample columns in their emitted order.
- `vcfeval` parity requires exact `summary.txt` equality and exact decompressed
  bodies for `tp`, `tp-baseline`, `fp`, and `fn` category VCFs.
- A native-hard versus gVCF-hardcut difference is reported as a construction-
  path distinction, not as a regression in `1.7.1i`.
- Any missing input, tool, index, tag, commit, or expected output fails hard.
- Jobs are monitored only; no cancellation, requeue, node, partition, or Slurm
  service action is authorized by this ledger.

## Existing-evidence result reused for issue 29

The completed CLI 1.7.0 HG003 5x/5x study reported:

| Callset | TP call | FP | FN | Precision | Sensitivity | F1 |
|---|---:|---:|---:|---:|---:|---:|
| Raw CLI gVCF | 3,604,748 | 17,651 | 227,142 | 0.9951 | 0.9407 | 0.9672 |
| GVCFtyper hard from that gVCF | 3,604,748 | 17,651 | 227,142 | 0.9951 | 0.9407 | 0.9672 |
| Native CLI hard | 3,603,895 | 17,202 | 227,997 | 0.9952 | 0.9405 | 0.9671 |

After `bcftools norm -f REF -m -both`, native hard versus GVCFtyper hard had
953,551 native-only, 5,018 derived-only, and 4,773,983 shared records. Of the
native-only records, 925,199 were `MLrejected`. These data establish the
construction-path distinction but do not substitute for the still-missing
exact upstream-1.7.0 versus released-1.7.1i gVCF parity lane.

## Continuation handoff

The exact live-job snapshot, source/input contracts, safe resume procedure,
publication paths, and closeout checklist are recorded in
`docs/plans/20260801T111727Z_hg003_gvcf_validation_handoff.md`. The handoff was
created while jobs 2606 and 2611 were running and job 2612 was validly held on
their `afterok` dependency; it does not authorize manipulation of those jobs or
the stale dependency-only jobs 2600 and 2608.

## Post-handoff dependency diagnosis at 2026-08-01T17:19:33Z

| Child | Dependency | Why it can never run |
|---:|---|---|
| 2600 | `afterok:2598:2599` | Both parents failed before CLI execution with exit `2:0`. |
| 2608 | `afterok:2606:2607` | Parent 2607 failed preflight with exit `2:0`; parent 2606 later also failed post-run. |
| 2612 | `afterok:2606:2611` | Both completed direct lanes exited `2:0` at the same post-run index-count gate. |

Jobs 2606 and 2611 completed their expensive CLI and VCF-conversion stages,
and each runner successfully passed BGZF integrity, contig-list, and sample-list
checks. Both then stopped on `ERROR: invalid indexed record count: 0`. No gVCF
or comparison result directory was published.

The zero was index metadata, not evidence of an empty VCF. Sentieon's emitted
TBI is queryable but reports zero through `bcftools index --nrecords`. A bounded
headnode reproduction against the existing official native-hard VCF returned
zero from its Sentieon-emitted TBI; rebuilding a separate TBI with the pinned
bcftools took 2.68 seconds and returned the correct 5,661,729 records. The
direct runner therefore now force-rebuilds its TBI with the pinned bcftools
before applying the nonzero record-count publication gate.

Scheduler work remains intentionally separate: jobs 2600, 2608, and 2612 have
not been canceled or altered as part of this diagnosis. After the user receives
and explicitly approves the exact scheduler proposal, cancel only those three
stale children, submit corrected replacements for direct jobs 2606 and 2611,
and submit one comparison job with `afterok` on those two new direct IDs.
