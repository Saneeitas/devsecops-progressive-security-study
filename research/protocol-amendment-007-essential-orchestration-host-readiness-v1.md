# PA-007 — Essential Orchestration and Host-Readiness Clarification

**APPROVED — PI approval recorded October 13, 2026 — EXECUTION REQUIRES A SEPARATE PASSING READINESS GATE**

- **Amendment ID:** PA-007
- **Principal Investigator:** Muhammad Sani Ibrahim
- **Research governance:** independent, PI-led
- **Approval date:** October 13, 2026
- **Approval status:** APPROVED
- **Approval source:** explicit PI declaration in the research conversation
- **Approved revised proposal-package manifest SHA-256:** `0fec7e1d764de56175c429150f04ab589951cc1e6e1ba125c0f66c8fcb3648df`
- **Effective point:** immediately before the first remaining Block 7 observation, `C5-R007`.
- **Scope:** external readiness/orchestration controls only. The frozen experimental runner and all scientific treatments remain unchanged.

## Purpose

PA-003 requires checks for host contention and memory concerns. PA-005 permits low-impact VS Code, Codex, Docker Desktop, Chrome, terminal, and documentation activity. PA-006 retains host stability, OS performance health, power eligibility, and sleep inhibition as gates. This amendment fixes the **external decision procedure**, not experimental treatment: it distinguishes essential orchestration from unrelated work and defines fixed host-level CPU and active-memory-pressure rules before additional outcomes are observed.

## Essential roles and prohibited work

VS Code, the Codex controller and helpers needed to operate the study, Docker Desktop, and project-owned containers required by the approved runner are essential orchestration/infrastructure. Their presence or their individual per-process CPU values alone does not establish competing workload.

The PA-005 prohibitions remain: unrelated builds, scans, large unrelated transfers, heavy computation, unrelated Docker workloads, and deliberate workload manipulation in response to duration, finding, or gate results. A recorded essential process can still lead to NO-GO through the fixed host-capacity rules below.

## Fixed CPU rule

This Mac has eight logical CPUs. Let `u = 100 / logical_CPU_count = 12.5` percentage points of total host CPU capacity. At fixed offsets of approximately 0, 30, and 60 seconds, take a five-second `top` sample and record its total CPU idle percentage.

- **CPU GO:** all three samples have idle capacity at least `2u` (25%), and no worsening condition applies.
- **Sustained saturation NO-GO:** all three samples have idle capacity below `u` (12.5%).
- **Worsening-trend NO-GO:** idle capacity is non-increasing across the three samples and the first-to-last decline is at least `u` (12.5 percentage points).
- **Borderline NO-GO:** every remaining CPU pattern, including any sample below `2u`, is a NO-GO for that observation. Record it and conduct a new complete window later; do not reinterpret a borderline window after outcome information appears.

`u` is derived from one full logical CPU on the observed eight-logical-CPU host; no pilot or final outcome informed this rule. Process percentages are not summed because macOS reports them relative to logical CPUs and they do not equal host saturation.

## Fixed memory rule

At each CPU sampling point collect `memory_pressure` and `vm_stat`.

- **Memory GO:** every `memory_pressure` sample reports zero throttled pages, the required fields parse successfully, and both `vm_stat` pageout deltas equal zero for the two sample intervals.
- **Active-pressure NO-GO:** any nonzero throttled-page count, or positive pageout deltas in both consecutive intervals.
- **Borderline memory NO-GO:** exactly one positive pageout interval, missing required field, command failure, or a counter discontinuity. A discontinuity is a negative `Pageouts` delta, which indicates a reset/reboot or inconsistent samples. Repeat a full new window later; do not launch from a borderline window.

`vm.swapusage`, swapins, and swapouts are retained as context but are not pass/fail measures: the latter are cumulative counters and the former includes allocated swap. The rule uses current pressure (`Pages throttled`) and time-window pageout change instead.

## Existing mandatory safeguards retained

A GO also requires all pre-existing safeguards: `CPU_Scheduler_Limit = 100`, `CPU_Speed_Limit = 100`, no macOS thermal/performance warning, PA-006 power eligibility and Low Power Mode off, process-bound sleep inhibition, Docker/cache/artifact readiness, sufficient storage, no stale project resources, schedule/provenance integrity, and no prohibited unrelated workload. Any contradictory or unavailable required measurement is NO-GO.

## Prospective consistency and reporting

The rule set, commands, offsets, calculations, and role classification template are fixed in the approved external PA-007 procedure before any new run. No value may be changed based on duration, scanner output, finding count, or gate outcome. It applies identically to every future unstarted observation.

C3-R007, C2-R007, and C4-R007 remain valid and unchanged. The Block 7 partial checkpoint remains preserved. The final report must disclose that this external readiness clarification began mid-block; it does not authorize reruns, reclassification, interim analysis, or changes to the primary model.

## Rollback and stop

Stop before an observation on any NO-GO. Preserve all diagnostics externally. Any change to these rules needs a further prospective amendment; no temporary waiver, outcome-based adaptation, or silent fallback is allowed.
