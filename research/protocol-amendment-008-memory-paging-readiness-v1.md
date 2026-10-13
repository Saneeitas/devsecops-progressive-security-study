# PA-008 — Combined Active-Memory Readiness Policy

**APPROVED — PI approval recorded October 13, 2026 — EXECUTION REQUIRES A SEPARATE PASSING READINESS GATE**

- **Amendment ID:** PA-008
- **Principal Investigator:** Muhammad Sani Ibrahim
- **Research governance:** independent, PI-led
- **Approval date:** October 13, 2026
- **Approval status:** APPROVED
- **Approval source:** explicit PI declaration in the research conversation
- **Approved package manifest SHA-256:** `2bb0be61760377d8e8247b68bc47900842a8a9399d6f3ee4a035d5c247310c10`
- **Effective point:** after this amendment is frozen and before `C5-R007`.
- **Scope:** external host-readiness orchestration only; no historical run is changed.

## Proposed combined memory decision

Retain PA-007's three timestamped samples, all CPU rules, OS-performance NO-GO, PA-006 power and sleep conditions, Docker/cache/artifact checks, storage, schedule/provenance integrity, and prohibited-workload restriction.

For each sample interval, calculate `Pageouts_delta / actual_elapsed_seconds` and record device page size.

A **memory GO** requires every condition below:

1. `Pages throttled = 0` at every sample.
2. `Pageouts` is monotonic nondecreasing; any negative delta is a counter-discontinuity NO-GO.
3. Each pageout rate is at most **42 pages/s** (172,032 bytes/s for 4,096-byte pages).
4. `vm_stat` Swapouts does not increase from first to final sample.
5. All counters, timestamps, and pressure fields are complete and internally consistent.

A rate above 42 pages/s, any nonzero throttling, any swapout increase, counter discontinuity, unavailable/contradictory measurement, or other PA-003–PA-007 failure is NO-GO. A positive rate at or below the ceiling is recorded but does not alone block execution.

## Safeguards against adaptation

The threshold and conjunction are fixed before another outcome is observed. They may not be adjusted in response to duration, findings, scanner output, or gate status. The same external procedure must be used before every unstarted observation. The policy does not turn paging into an experimental outcome.

## Effective point and disclosure

PA-008 applies prospectively after its approved freeze and before the next unstarted Block 7 slot, C5-R007. The report must disclose the PA-007/PA-008 transition, all readiness delays, and the retained prior NO-GO records. It does not authorize execution by itself.
