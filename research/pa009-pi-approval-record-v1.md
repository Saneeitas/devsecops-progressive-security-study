# PA-009 PI approval record — FINALIZED

- Amendment: PA-009 — Exceptional Recovery of the C5-R007 Pre-Measurement Cache-Preflight Failure
- Principal Investigator: Muhammad Sani Ibrahim
- Approval date: October 13, 2026
- Approval source: explicit PI declaration (Conditional PI Approval — PA-009 Single-Slot Recovery, accepted in full)
- Approved proposal-package manifest SHA-256: `2f6ad76f6c4885e65b9d110fc645fceb4bfbfbc6dc9aa28c144d860064d971d2`
- Parent commit at freeze: `e7f3bb4657636eba72780470c4b903e5c6212844` (`final-study-pa008-v1`)
- Preconditions verified (§2.1–§2.7): package manifest OK (5/5); HEAD/tag/amendment/lineage match; six C5-R007 hashes match; zero measurement confirmed; no VALID for slot; schedule + dataset validators PASS.
- Implementation checksums at freeze: `pipeline/experiment.py 094cc649e950997bc03f31f5f22e6bc9a5ca5e6d7d011f1af2a8b6c76e4d6686`; `pipeline/validate-experiment.py ddb76839c438ce3d616e09bd518aa6e3260e7000a0381754d0736c65131c1cb4`.
- Regression: 12/12 synthetic checks PASS; global validators PASS; preflight PASS 15/15 with one disclosed transient exit-2 (unreproduced, streams captured).
- Effective point: prospectively after freeze, before `C5-R007-A02`.
- Authorizations on freeze: implementation + verification + freezing ONLY. Execution of `C5-R007-A02`, `C6/C1/C0-R007`, or any Block 8 observation is NOT authorized by this record.
- Cache hardening is NOT included (separate scope, unapproved).
