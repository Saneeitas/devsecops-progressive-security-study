# PA-003 final invalid-attempt policy

**APPROVED — PA-003 — October 10, 2026**

Source-document provenance: explicit PI declaration in the ChatGPT research conversation on October 10, 2026; based on the revised PA-003 package and approved-candidate schedule.

Each slot has one original attempt and up to A02/A03 replacements. A replacement is allowed only after its immediate predecessor is `INVALID_RETRYABLE` for an eligible mechanical reason: infrastructure startup, unexpected functional-test failure, required scanner execution/output failure, normalization failure, resource isolation failure, or lifecycle/cleanup failure.

Findings, missed vulnerabilities, severity, gate result, unfavorable performance, and slow VALID runs never justify replacement. `INVALID_NONRETRYABLE` attempts are not automatically retried. At most one VALID observation may fill a slot. Preserve every attempt and its PA-003 provenance.

On exhaustion or an incomplete block, stop collection for review. Do not silently reduce the 20-block target or claim the planned primary precision.
