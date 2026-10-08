# Validated Experimental Pipeline v1 Freeze

**Freeze date:** 2026-10-08  
**Branch:** `experiment/pipeline-implementation-v1`

## Lineage

| Checkpoint | Tag | Target commit |
| --- | --- | --- |
| Secure baseline | `secure-baseline-v2` | `7067c5b2bf862893056959b0c15cd04d15cf183f` |
| Verified corpus | `corpus-v1` | `eeb2e772ffb60fb214df8b41866be23be89dcf3f` |
| Original specification | `experiment-spec-v1` | `d808bfc24691ace15c0bbdc2a914a8ce01e6059b` |
| OSV amendment | `experiment-spec-pa001` | `d12a5035ab79239e0eff65840647e39433ccbef4` |
| Validated implementation | pending `pipeline-v1` tag | `556a634d283f11d906b267ba6b2ba5a4864a80f7` |

The implementation commit descends from PA-001. PA-001 is authoritative only
for the OSV-Scanner 2.6.0 offline local-cache invocation and placement. The
secure baseline, corpus, original specification, and PA-001 tags are preserved
without movement.

## Validated smoke execution

Smoke data are engineering evidence only and are excluded from both the pilot
and final experimental datasets.

| Run | Status | Freeze relevance |
| --- | --- | --- |
| C0-R001 | `INVALID_RETRYABLE` | Historical retained attempt |
| C0-R002 | `INVALID_RETRYABLE` | Historical retained attempt |
| C0-R003 | `VALID` | Validated common C0 lifecycle |
| C6-R001 | `INVALID_RETRYABLE` | Historical retained attempt |
| C6-R002 | `INVALID_RETRYABLE` | Historical retained attempt |
| C6-R003 | `INVALID_RETRYABLE` | Historical retained attempt |
| C6-R004 | `VALID` | Validated complete C6 lifecycle |

C6-R004 used pipeline commit `556a634d283f11d906b267ba6b2ba5a4864a80f7`.
It completed the common lifecycle, all cumulative controls, normalization, gate
evaluation, DAST user/admin passes, secret-artifact check, and cleanup. The
retained functional invariant was exactly 12 tests: 11 passed, with the single
expected V04 regression named `does not disclose another user's order`.

No vulnerability-detection interpretation, seeded-vulnerability mapping, or
coverage calculation is made by this freeze record.

## Frozen treatment

The configurations in `research/configurations.json` remain cumulative: C0 has
no controls; C1 adds SAST; C2 adds SCA; C3 adds secret scanning; C4 adds
container vulnerability scanning; C5 adds Terraform IaC scanning; and C6 adds
DAST.

| Control | Frozen implementation |
| --- | --- |
| SAST | Semgrep 1.178.0 |
| SCA | OSV-Scanner 2.6.0 with PA-001 offline cache placement |
| Secret scanning | Gitleaks 8.30.1 |
| Container vulnerability scanning | Trivy 0.74.0 |
| IaC scanning | Checkov 3.3.8 |
| DAST | OWASP ZAP 2.17.0 |

`research/experiment-artifacts-v1.json` remains the authoritative identity
manifest for pinned images, rules, advisory and vulnerability databases,
scanner configurations, OpenAPI, ZAP add-ons, DAST data/context, and contract.
The audit verified all repository checksums. Runtime preflight also verified the
unchanged OSV archive and frozen Trivy database before and after C6-R004.

## Measurement and gate semantics

The harness records monotonic wall-clock total duration, setup and database
sub-stages, dependency preparation, build, tests, container build, each control
duration, DAST preparation/startup, each ZAP pass, native exit codes, execution
status, cache state, environment metadata, raw output paths, and normalized
finding counts. Failed and invalid runs remain retained rather than overwritten.

CPU utilization and peak-memory fields are nullable by the frozen run schema
and the protocol requires them only where practical. C6-R004 correctly records
these fields as unavailable (`null` with `measurement_available: false`), while
its primary operational duration measurements are complete. This is a limitation
to report for pilot/final analysis; it does not invalidate duration-based
primary operational measures.

The synthetic gate is distinct from scanner execution and finding presence. It
returns `ERROR` for execution/normalization failures, `FAIL` only for normalized
findings already classified as `SEEDED_TRUE_POSITIVE` or
`NON_SEEDED_VALID_FINDING`, and `PASS` otherwise. C6-R004's `PASS` is consistent
with this policy because its normalized findings remain `UNRESOLVED` pending the
separate manual mapping process. A valid run and a gate result are not coverage
or effectiveness conclusions.

## Pilot schedule and research restrictions

`research/pilot-schedule-v1.csv` has 35 entries: five balanced blocks, each
containing C0-C6 exactly once. IDs are unique and deterministic from R001
through R005. Validation passed at freeze time.

No pilot or final run has occurred. Before collection, do not change the corpus,
V01-V12 definitions, application behavior, tool versions, rules, advisory data,
Trivy database, scanner configurations, OpenAPI, DAST contract, timing
boundaries, gate policy, mapping rules, cache policy, or schedule without a
documented protocol amendment or a new experiment version.

## Smoke evidence preservation

At freeze time, smoke evidence is retained locally under `data/raw/smoke/` and
is excluded from `data/raw/pilot/` and `data/raw/final/`. It is untracked by Git
and therefore is **not yet durable remote research evidence**. This is a
preservation risk, not a reason to alter historical records or commit potentially
sensitive raw reports into the source repository.

Before pilot collection, create an immutable encrypted archive outside this
repository, retain its per-file SHA-256 manifest, and store the archive and
manifest in approved access-controlled research storage. The local manifest
created during this audit covered 177 smoke-evidence files and had SHA-256:

`d5269323de135b2dd408d00b6c5a9dde01b9a8122b46591fd44c23fcc0577d9c`

Verify the archived manifest against that value, record the archive location and
access controls in the research log, and retain the local evidence until archive
verification is complete. Do not mix these smoke records with pilot or final
data.
