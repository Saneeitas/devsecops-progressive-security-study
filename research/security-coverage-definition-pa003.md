# PA-003 security-coverage definitions

**APPROVED — PA-003 — October 10, 2026**

Source-document provenance: explicit PI declaration in the ChatGPT research conversation on October 10, 2026; based on the revised PA-003 package and approved-candidate schedule.

Eligibility is `(scanner, seeded_vulnerability_id)`; the per-run matrix key is `(run_id, configuration, scanner, seeded_vulnerability_id)`. Outcomes are `DETECTED`, `NOT_DETECTED`, `UNRESOLVED`, and `OUT_OF_SCOPE`; detection requires adjudicated evidence.

Scanner coverage is unique eligible seeds detected divided by eligible seeds. Configuration coverage is unique seeds detected by at least one included scanner divided by its defined eligible seed set. Marginal coverage is newly detected unique seeds. Repeat detections do not add unique seeds; report detection reliability/inconsistency separately. C0 has a zero-scanner denominator and no detection ratio. Keep alerts, unique findings, seed detections, false positives, unresolved alerts, and out-of-scope findings separate.
