# PA-005 — Controlled background workload policy clarification

**APPROVED — PI approval recorded October 11, 2026 — EXECUTION NOT AUTHORIZED BY THIS RECORD**

- **Amendment ID:** PA-005
- **Classification:** prospective environmental-control clarification
- **Principal Investigator:** Muhammad Sani Ibrahim
- **Research governance:** independent, PI-led
- **Approval authority:** Principal Investigator
- **Approval date:** October 11, 2026
- **Approval decision:** APPROVED
- **Approval source:** explicit PI declaration in the research conversation
- **Effective point:** after `C2-R001`, `C0-R001`, and `C6-R001` and before any subsequent final-study observation

## Purpose and scope

PA-003 requires host-contention checks and competing-activity recording but does not categorically prohibit ordinary interactive applications. PA-005 prospectively clarifies which ordinary background use is compatible with those controls. It does not add a security control or alter experimental timing, measurement, corpus, schedule, statistical analysis, sample size, validity model, or historical evidence.

## Permitted activity

The following may remain open or be used at normal, low impact for research purposes during a measured run:

- Chrome for ChatGPT and research communication;
- VS Code for experiment management and monitoring;
- Docker Desktop as approved experimental infrastructure;
- normal macOS background services;
- lightweight documentation and terminal activity.

An application being open does not by itself constitute material host contention.

## Prohibited activity during measured runs

- unrelated software builds;
- unrelated vulnerability scans;
- large unrelated downloads or uploads;
- heavy unrelated computation;
- additional unrelated Docker workloads;
- deliberately changing host load in response to observed pipeline duration, findings, or gate outcomes.

## Environmental documentation

Use existing PA-003 readiness procedures and record AC-power status, host stability assessment, material competing workloads, memory-pressure or swap concerns, Docker health, Resource Saver status, significant interruptions, and environmental deviations. These remain environmental metadata. CPU utilization, RAM usage, and unrelated-application consumption are not new primary or secondary experimental outcomes, and the pipeline timing instrumentation remains unchanged.

## Scientific integrity and comparability

The first three Block 1 observations precede PA-005; Block 1 was interrupted before the remaining slots. The final report will disclose both the interruption and this prospective clarification. All previously VALID observations remain retained and valid unless an independently established protocol-validity defect is found. No observation is rerun because it appears slow or fast, no interim treatment-effect analysis is authorized, and the approved 20-block schedule remains unchanged.

## Cache and execution boundary

PA-005 does not change the controlled warm-cache policy. Cache provenance remains commit-bound. If preparation is separately authorized, use the existing non-measured warm procedure; do not manually edit its record. PA-005 approval alone does not authorize a final-study observation.
