# Experiment invariants

The following conditions are frozen for final experimentation. Changing one requires a documented amendment and, where comparability is broken, a new experiment version and separate dataset.

| Invariant | Frozen requirement |
|---|---|
| Corpus commit | `eeb2e772ffb60fb214df8b41866be23be89dcf3f` (`corpus-v1`) |
| Vulnerability definitions | V01–V12 definitions, locations, mappings, and ground truth remain unchanged |
| Application behavior | Application, tests, dependencies, Dockerfile, Compose, and Terraform corpus fixtures remain byte-equivalent to `corpus-v1`, except separately versioned pipeline-only files |
| Tool versions | Every scanner/runtime wrapper/image/database is pinned exactly before pilot/final execution; no floating `latest` |
| Scanner configurations | Rulesets, exclusions, severity thresholds, targets, timeouts, and update databases are pinned and checksummed where practical |
| Pipeline configurations | C0–C6 remain cumulative exactly as defined in `research/configurations.json` |
| Runner/environment policy | Runner class, OS, architecture, resource class, service versions, network policy, and execution ordering/randomization are fixed and recorded |
| Cache policy | Controlled warm-cache priming and cache-state recording are used; cold-cache runs require a separate condition |
| Timing methodology | Monotonic wall-clock boundaries and stage definitions in the protocol remain fixed |
| Finding normalization | Deduplication keys, severity mapping, location handling, corpus mapping, and adjudication rules are versioned and frozen before results |

The pipeline commit SHA, run metadata, deviations, failures, and tool exit results must be recorded for every run. Raw scanner output is immutable. Pilot records cannot enter the final dataset. No insecure Terraform is deployed as part of this experiment.
