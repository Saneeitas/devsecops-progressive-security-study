# PA-002 — Invalid-Run Replacement and Censoring Policy

## Identification and effective point

- **Amendment ID:** PA-002
- **Type:** methodological and operational clarification
- **Effective point:** after seven valid pilot runs and one invalid pilot attempt, before the first replacement attempt and before resumption of pilot block 2
- **Authoritative implementation:** provenance-only support in `pipeline/experiment.py`, `pipeline/validate-experiment.py`, and `data/schema/run.schema.json`

PA-002 is introduced after pilot collection began. It does not retroactively alter
the original protocol, the original 35 scheduled slots, or any historical record.
It supplies missing replacement and censoring rules so future invalid attempts are
handled reproducibly and without reference to security outcomes.

## Trigger and scope

The trigger was scheduled slot `P-C1-R002`, classified
`INVALID_RETRYABLE` following `UNEXPECTED_FUNCTIONAL_TEST_FAILURE`. The frozen
functional invariant expected 12 tests, 11 passing, and the one retained V04
failure. The observed attempt had 12 tests, 10 passing, and two failures: the
expected V04 result plus a five-second timeout in the registration/duplicate-email
test. No scanner executed and no security finding motivated this amendment.

The root cause is unresolved. Unusually slow database readiness, dependency
preparation, and functional-test execution make transient host/runtime slowdown a
plausible explanation with moderate, non-conclusive confidence. PA-002 does not
change the test, its five-second timeout, application behavior, or validity rules.

## Replacement eligibility

Only an attempt already classified `INVALID_RETRYABLE` under the frozen validity
rules may receive a replacement. Eligible reasons are:

- infrastructure startup failure;
- unexpected functional-test failure;
- required scanner execution failure;
- missing or corrupt required scanner output;
- normalization failure;
- resource-isolation failure; and
- lifecycle or cleanup failure that invalidates the attempt.

Replacement is prohibited for vulnerability detections or counts, missed seeded
vulnerabilities, finding severity, valid security outcomes, security-gate `FAIL`,
valid slow execution, or unfavorable performance results. A scanner's normal
finding-related exit status is not a scanner execution failure. An
`INVALID_NONRETRYABLE` attempt is never retried automatically.

## Attempt limit and timing

Each scheduled slot has at most three attempts: its original attempt and up to two
replacements. A valid replacement closes the slot. If all three attempts are
invalid, preserve all evidence, mark the slot incomplete, stop the current block,
and require explicit methodological review before further execution. Unlimited
retries are prohibited.

Replacement occurs before advancing to the next original scheduled slot. For the
current slot, PA-002 requires: complete this amendment; perform non-measured
environmental readiness checks; execute the linked replacement; validate it; and
advance to `P-C2-R002` only if the replacement is valid. If it is invalid but
retryable, retain it and use the one remaining attempt allowance. The original
35-slot schedule is immutable; replacements are linked attempts, not new slots.

## Identifier and provenance convention

Replacement IDs are immutable suffixes on the original scheduled slot:

| Attempt | Identifier |
| --- | --- |
| Original | `P-C1-R002` |
| First replacement | `P-C1-R002-A02` |
| Second replacement | `P-C1-R002-A03` |

The harness accepts only pilot replacement suffixes `-A02` and `-A03`. It rejects
an attempt whose configuration, scheduled order, original slot, predecessor, or
eligible reason does not match PA-002. It also requires immutable predecessor
evidence classified `INVALID_RETRYABLE` before a replacement can start.

Each replacement record includes optional `replacement_provenance` metadata:

- original scheduled slot ID and configuration;
- scheduled order;
- attempt number and predecessor attempt ID;
- eligible replacement reason;
- evidence directory; and
- protocol amendment reference `PA-002`.

The standard run timestamp and pipeline timing fields provide start and end times;
the root validity field records the resulting classification. The original attempt
is never rewritten. Historical records have no fabricated provenance fields and
remain valid under the backward-compatible schema.

## Measurement, reporting, and censoring

Each original scheduled slot contributes at most one valid observation to primary
pilot or final completed-pipeline comparisons. A valid replacement fills its
original slot; an invalid attempt does not become a completed configuration
measurement. Invalid attempts remain in the historical dataset for attempt counts,
invalidity rates, failure-stage/reason analysis, replacement frequency,
infrastructure reliability, and sensitivity analysis. Partial timings may be
described but do not become completed-pipeline duration measurements. Missing
scanner outputs are never represented as zero findings, and unavailable CPU or
peak-memory measurements remain `null`.

Timeout-related invalidity can be informative censoring: excluding slow invalid
attempts may underestimate pipeline overhead. Future reporting must provide total,
valid, invalid, and replacement attempt counts; failure stage; timeout-related and
configuration-specific invalidity; exhausted slots; primary valid-run performance;
and sensitivity to invalid-attempt handling. Security-control overhead and
environmental instability must be reported separately.

## Treatment preservation and governance

PA-001 corrected OSV-Scanner 2.6.0 offline-cache invocation before OSV corpus
outcomes. PA-002 is different: it is a prospective post-collection-start policy
clarification for invalid-run replacement and censoring. It changes no scanner,
rule, database, test, application behavior, corpus item, OpenAPI contract, DAST
behavior, gate, finding mapping, measurement boundary, or schedule.

`pipeline-v1`, `experiment-spec-v1`, and `experiment-spec-pa001` remain unchanged.
This amendment is separately committed and tagged. Any later deviation requires a
new documented amendment before executing the affected attempt.
