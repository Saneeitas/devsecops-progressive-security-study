# PA-009 — Exceptional Recovery of the C5-R007 Pre-Measurement Cache-Preflight Failure

**APPROVED — PI approval recorded October 13, 2026 — EXECUTION OF C5-R007-A02 REQUIRES A SEPARATE PI DECISION AND A FRESH PASSING PA-008 GATE**

- **Amendment ID:** PA-009
- **Principal Investigator:** Muhammad Sani Ibrahim
- **Research governance:** independent, PI-led
- **Approval date:** October 13, 2026
- **Approval status:** APPROVED (conditional approval satisfied; see approval record)
- **Approval source:** explicit PI declaration in the research conversation (Conditional PI Approval — PA-009 Single-Slot Recovery)
- **Approved proposal-package manifest SHA-256:** `2f6ad76f6c4885e65b9d110fc645fceb4bfbfbc6dc9aa28c144d860064d971d2`
- **Effective point:** prospectively after this amendment is frozen and before `C5-R007-A02`.
- **Scope:** single-slot prospective exception only: original attempt `C5-R007` → linked replacement `C5-R007-A02`. No other slot, no Block 8, no `-A03`.

## Background

`C5-R007` (C5, Block 7) was attempted after a passing PA-008 gate. The frozen runner refused measurement at `cache_preflight`: `data/cache-preflight.json` pinned `source_commit 41d0a23` while HEAD had advanced to `e7f3bb4` via documentation-only PA-007/PA-008 commits. All image IDs, lockfile, and policy matched. The runner wrote `INVALID_NONRETRYABLE`, `failure_stage cache_preflight`, `total_ms 0`, zero stages/controls/tools/findings, gate `NOT_APPLICABLE`, empty `raw/`. The cache was renewed under separate PI authorization. The INVALID record is preserved byte-identical (run.json SHA-256 `3c8a030cfa0121ef8932799f182d92c92a9ed0b8b75dd083a00cf325ad13147d`).

## Acknowledged prohibition

PA-003 §7–§9 and PA-002 §§29–46 prohibit this replacement; the frozen harness enforced it. PA-009 does not reinterpret or retrospectively alter those rules. It creates one prospective, PI-approved exception carrying its own `PA-009` provenance marker. Every other slot keeps existing behavior.

## One-time exception rule (exact)

`C5-R007-A02` may execute iff: classification `final`, config `C5`, original `C5-R007`, frozen Block 7 scheduled order, attempt 2, predecessor `C5-R007`, reason `infrastructure_startup_failure`, predecessor byte-verified against the six pinned SHA-256 hashes with zero-measurement fields (`total_ms 0`, empty execution/controls/tools, zero findings, gate `NOT_APPLICABLE`, empty `raw/`, no prior provenance), `protocol_amendment PA-009`, and no existing VALID for the slot. At most this one `-A02`; if not VALID, Block 7 stops for PI review. Any other `INVALID_NONRETRYABLE` predecessor continues to raise.

## Implementation record

Two gated additions, nothing else changed (diff reviewed; no scanner, timing, stage, schedule, or analysis code touched):

- `pipeline/experiment.py`: `PA009_*` constants, `pa009_exception()`, one conditional in `replacement_provenance()`, `PA-009` provenance marker.
- `pipeline/validate-experiment.py`: mirrored constants, `pa009_final_exception()`, one branch in `final_provenance()`.
- Regression: 12/12 synthetic checks pass (accept exact case; reject wrong slot, tampered/missing predecessor, incomplete provenance, forged cross-slot marker, second VALID, unauthorized A03; pilot PA-002 and original-ID paths unchanged); global `--runs`/`--schedule` PASS; artifact preflight PASS 15/15 (one transient exit-2 observed once during verification with stderr discarded; 10 subsequent captured runs exit 0 with identical output — see implementation evidence; preflight must be re-verified before any future run).

## Safeguards and disclosure

Original evidence/classification/reason immutable; frozen C5 configuration and Block 7 order preserved; 45 VALID observations untouched; no outcome-driven decision (no outcome exists); fresh PA-008/power/cache/Docker/functional/scanner/cleanup gates required before any `C5-R007-A02` execution. On success the final report discloses the HEAD drift, cache renewal (postgres/base IDs unchanged), the INVALID record, this exception, all readiness outcomes, and the Codex-to-OpenCode transition. On decline/failure, Block 7 closes 6/7 with pre-specified 19-block primary handling (PA-003 §11).
