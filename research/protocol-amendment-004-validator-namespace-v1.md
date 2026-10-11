# PA-004 — Dataset validator classification namespace correction

**APPROVED — PI approval recorded October 11, 2026 — EXECUTION NOT AUTHORIZED BY THIS RECORD**

- **Amendment ID:** PA-004
- **Type:** post-freeze implementation defect correction; provenance and validation only
- **Discovery point:** PA-003 final-study Block 1, after three retained VALID observations
- **Principal Investigator:** Muhammad Sani Ibrahim
- **Research governance:** independent, PI-led
- **Approval date:** October 11, 2026
- **Approval decision:** APPROVED
- **Approval source:** explicit PI declaration in the research conversation
- **PI approval status:** APPROVED

## Approval scope

The PI approved this narrowly scoped, provenance-only correction after reviewing the retained evidence and regression plan. The approval authorizes finalization and corrective freezing of PA-004. It does **not** authorize further Block 1 collection, any final-study observation, a scanner execution, or a change to an experimental treatment.

## Defect and root cause

`pipeline/validate-experiment.py` registered every evidence-directory name in one global `ids` set. Its uniqueness key was therefore `run_id` alone. The evidence classifications (`smoke`, `pilot`, and `final`) are separate namespaces, but final schedule identifiers deliberately use names such as `C0-R001` and `C6-R001`, which also occur in the historical smoke dataset. Consequently, global `--runs` validation rejected valid final evidence solely because an identically named smoke observation existed.

The defect appeared after retained final observations `C2-R001`, `C0-R001`, and `C6-R001`. It does not concern a duplicate within one classification, a schedule-membership failure, scanner execution, or a security finding.

## Proposed correction

Replace the validator identity key from `run_id` with `(classification, run_id)`. The validator continues to reject duplicate IDs within a classification and retains all final-schedule, configuration/order, A02/A03 provenance, maximum-attempt, single-VALID-slot, evidence-completeness, and validity checks.

Changed repository files:

- `pipeline/validate-experiment.py`: add `register_run_identity()` and use its `(classification, run_id)` key in `runs()`.
- `pipeline/test_validate_experiment_namespaces.py`: synthetic regression coverage for the namespace rule.
- `research/protocol-amendment-004-validator-namespace-v1.md`: this approved amendment record.

No scanner command, tool version, scanner scope, timing boundary, functional test, Docker behavior, corpus item, gate rule, mapping rule, schedule, or raw evidence is changed.

## Before and after

Before, `smoke/C0-R001` and `final/C0-R001` caused a false duplicate assertion. After, they are accepted because they have identities `("smoke", "C0-R001")` and `("final", "C0-R001")`. Two occurrences of `C0-R001` in `final` remain rejected.

## Evidence and scientific impact

The three Block-1 records remain immutable, with their existing raw reports, run metadata, and checkpoint archive. This correction changes only the validator’s namespace interpretation and does not alter an observation, primary estimand, treatment, measurement, or analysis rule. It is therefore a mechanical provenance correction with no intended scientific impact. PA-004 approval does not itself authorize final-study collection to resume; separate execution authorization is required.

## Validation required and completed for review

Targeted synthetic namespace, PA-002, and PA-003 provenance tests pass. Retained global dataset validation, pilot schedule validation, JSON Schema validation, approved final schedule checksum verification, and frozen-artifact preflight pass. The PA-003 freeze manifest continues to identify the pre-correction validator hash and remains historically unchanged; this approved PA-004 record identifies the corrective validator hash separately.
