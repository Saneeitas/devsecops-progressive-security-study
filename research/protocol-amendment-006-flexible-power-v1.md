# PA-006 — Flexible Power-Source and Host-Stability Policy

**APPROVED — PI approval recorded October 11, 2026 — EXECUTION REQUIRES A SEPARATE PASSING READINESS GATE**

- **Amendment ID:** PA-006
- **Classification:** substantive prospective environmental amendment
- **Principal Investigator:** Muhammad Sani Ibrahim
- **Research governance:** independent, PI-led
- **Approval date:** October 11, 2026
- **Approval status:** APPROVED
- **Approval source:** explicit PI declaration in the research conversation
- **Effective point:** after `C2-R001`, `C0-R001`, and `C6-R001`; before every subsequent final-study observation
- **Scope:** remaining Block 1 observations and future separately authorized blocks

## Policy

AC and battery operation are permitted. Immediately before every new observation, record the source, battery percentage where available, charging/discharging state, and the operating-system remaining-time estimate or its unavailability. AC operation remains subject to all existing readiness gates.

Battery operation requires all of the following:

1. battery charge at least 30%;
2. operating-system remaining-time estimate at least 45 minutes when available;
3. if no reliable estimate is available, battery charge at least 50%;
4. Low Power Mode disabled;
5. acceptable host stability, no material competing workload, healthy Docker/cache/artifacts, and verified process-bound sleep inhibition.

The 45-minute estimate is four times the pilot’s longest valid complete run, C6 at 664.122 seconds, providing a prospective reserve for cleanup and interruptions. These are pilot-derived readiness safeguards, not final-study outcome-derived thresholds.

A power-source transition during an observation is retained with its time and direction, then evaluated only under existing validity rules. It does not automatically invalidate, discard, or retry an observation. Prefer source changes between observations.

## Environmental provenance

Power source is environmental metadata, not a new experimental outcome. Maintain an external append-only record keyed by `(classification, run_id)` containing timestamp, source, battery percentage, charging state, remaining-time estimate/unavailability, Low Power Mode state, readiness decision, material background activity, and interruption details. Do not modify historical `run.json`, schema, raw reports, timing instrumentation, or the experimental runner to add power fields.

## Scientific integrity

PA-006 does not change scanner configurations, experimental treatments, the vulnerability corpus, approved schedule, sample size, timing instrumentation, primary statistical analysis, existing validity rules, or replacement rules. It does not assume AC and battery performance are equivalent. The first three Block 1 observations preceded PA-006 and remain VALID without backfilled power metadata. Final reporting must disclose the policy transition and potential power/order confounding; no interim treatment-effect or security-effectiveness inference is authorized.
