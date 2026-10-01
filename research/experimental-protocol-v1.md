# Experimental Protocol v1

## Frozen research state

- Secure baseline: `secure-baseline-v2` (`7067c5b2bf862893056959b0c15cd04d15cf183f`)
- Vulnerability corpus: `corpus-v1` (`eeb2e772ffb60fb214df8b41866be23be89dcf3f`)
- Protocol branch: `experiment/pipeline-protocol-v1`
- Corpus: V01–V12, frozen as `seeded_verified`

This protocol is defined before security-control execution or observation of scanner results.

## Objective, research questions, and hypotheses

The objective is to evaluate how progressively integrating automated security controls into the same CI/CD pipeline affects vulnerability-detection effectiveness, operational pipeline performance, marginal security benefit, and security-versus-overhead trade-offs.

- **RQ1:** How does progressive integration of automated security controls affect vulnerability detection coverage in a CI/CD pipeline?
- **RQ2:** How does progressive integration of automated security controls affect CI/CD operational performance?
- **RQ3:** What is the marginal security benefit associated with each additional security-control layer?
- **RQ4:** What trade-off exists between security effectiveness and operational overhead across different security-control configurations?

The following are hypotheses to test, not expected conclusions:

- **H1:** Progressive integration of security controls increases vulnerability detection coverage.
- **H2:** Progressive integration of security controls increases CI/CD execution time.
- **H3:** The marginal security benefit differs among security-control categories.
- **H4:** The relationship between security coverage and operational overhead is non-linear across security-control configurations.

## Progressive configurations and provisional tools

Configurations are cumulative. A configuration contains every control in its predecessors.

| Configuration | Enabled controls | Added control | Provisional implementation |
|---|---|---|---|
| C0 | None | None | Baseline CI/CD only |
| C1 | SAST | SAST | Semgrep `TO_BE_PINNED` |
| C2 | SAST + SCA | SCA | OSV-Scanner `TO_BE_PINNED` |
| C3 | SAST + SCA + Secret scanning | Secret scanning | Gitleaks `TO_BE_PINNED` |
| C4 | SAST + SCA + Secret scanning + Container scanning | Container scanning | Trivy `TO_BE_PINNED` |
| C5 | SAST + SCA + Secret scanning + Container scanning + IaC scanning | IaC scanning | Checkov `TO_BE_PINNED` |
| C6 | SAST + SCA + Secret scanning + Container scanning + IaC scanning + DAST | DAST | OWASP ZAP `TO_BE_PINNED` |

Exact versions and configurations will be frozen separately before experimentation; the latest version must not be selected automatically. Conclusions concern these selected implementations and cannot automatically be generalized to every tool in a category. Marginal contribution depends partly on this predefined ordering and must not be interpreted as the universal intrinsic value of the newly added category. Overlapping detections remain attributable to every detecting tool, while first detection is recorded by configuration.

## Experimental unit and run identity

One experimental unit is one complete execution of one specified pipeline configuration against the exact frozen `corpus-v1` application state. Each final run has ID `C<configuration>-R<run-number>`, using three-digit run numbers, such as `C0-R001`, `C1-R001`, and `C6-R025`.

Pilot runs use a separate `P-` namespace, such as `P-C0-R001`. Pilot records are stored separately and must never be merged into the final experimental dataset.

## Timing boundaries

All durations use monotonic-clock wall time and are recorded in milliseconds with explicit start and end timestamps where supported.

- **Pipeline start:** immediately before measured setup begins after runner allocation and source availability, using the same boundary for every configuration.
- **Dependency/setup:** from setup start through required runtime/tool initialization and dependency restoration or installation, ending before build begins.
- **Build:** invocation through completion of the application build.
- **Functional test:** invocation through completion of the unchanged functional-test stage.
- **Individual security control:** invocation through completion and artifact persistence for that control. Each tool receives a separate duration.
- **Deployment/startup:** start of local service/container preparation through readiness-check success or timeout.
- **DAST:** first DAST-specific action through scanner completion and artifact persistence; startup remains separate.
- **Pipeline end:** after all stages required by the configuration have completed and their result artifacts have been saved.
- **Total pipeline duration:** wall-clock elapsed time from pipeline start to pipeline end.

The total is measured directly. It is not inferred by summing stage or scanner durations because setup, teardown, persistence, overlap, and orchestration can make the sum differ from elapsed wall time. Failed and timed-out stages retain their measured durations and status.

## Security-effectiveness observations and classification

For each V01–V12 and configuration, record vulnerability ID, relevant expected controls, detected boolean, detecting tool, rule/check identifier, reported severity, finding location, and first configuration in which detection occurs. A vulnerability detected by multiple tools retains every tool association.

Every normalized scanner finding is classified as exactly one of:

- `SEEDED_TRUE_POSITIVE`: correctly maps to a seeded V01–V12 condition.
- `SEEDED_FALSE_NEGATIVE`: an in-scope seeded condition not detected by the evaluated control/configuration. This is represented in the vulnerability-detection mapping rather than invented as a scanner finding.
- `NON_SEEDED_VALID_FINDING`: valid security issue outside the seeded corpus.
- `FALSE_POSITIVE`: reported condition that manual validation determines is not present or security-relevant under the defined context.

Findings outside V01–V12 are not presumed false. Ambiguous findings require a recorded manual decision, reviewer/rationale, evidence reference, and validation timestamp. Raw outputs remain immutable; normalization and classification produce derived records.

## Security metrics

For a control or configuration scope, let `R` be the set of seeded vulnerabilities reasonably relevant to that evaluated scope and `D` the subset detected:

- **Scope-adjusted seeded detection coverage:** `|D ∩ R| / |R|`. Report `R` explicitly; do not compute when `|R| = 0`.
- **All-corpus coverage:** `number of distinct detected V01–V12 / 12`.
- **True positives (TP):** scanner findings validated as seeded or non-seeded valid findings, with seeded TP also reported separately.
- **False negatives (FN):** in-scope seeded vulnerabilities in `R` not detected.
- **False positives (FP):** normalized findings validated as false positives.
- **Precision:** `TP / (TP + FP)`, undefined when the denominator is zero.
- **Recall:** `TP_seeded / (TP_seeded + FN_seeded)` over the declared relevant set `R`. Out-of-scope corpus items do not penalize control-specific recall.
- **F1:** `2 × precision × recall / (precision + recall)`, undefined if required inputs or their sum are undefined/zero.
- **Marginal security gain:** `Coverage(Cn) - Coverage(Cn-1)`, reported for both scope-qualified and all-corpus coverage where meaningful.

Finding-level precision must use deduplicated normalized findings under the frozen normalization rules. Vulnerability-level recall uses distinct seeded vulnerabilities, not raw alert counts. Marginal gain describes this cumulative ordering and does not prove the intrinsic effectiveness of the newly added control because detections can overlap or depend on earlier stages.

## Operational measurements

Each run records total, setup, build, functional-test, each scanner, deployment/startup, and DAST durations; exit status; final security-gate result; CPU utilization and peak memory where practical; and raw and normalized finding counts by class/tool/severity.

Relative to the C0 aggregate reference:

- **Absolute overhead:** `Duration(Cn) - Duration(C0)`.
- **Relative overhead:** `(Duration(Cn) - Duration(C0)) / Duration(C0) × 100`.

For repeated runs, overhead uses prespecified comparable aggregate estimates (initially configuration medians with means and confidence intervals also reported), not arbitrary pairing of individual runs. If execution is deliberately blocked or paired, block-aware differences may additionally be reported. Resource measurement method, sampling interval, missingness, and platform limitations must accompany CPU/memory values.

## Environment metadata

Every run records run ID, configuration, corpus commit, pipeline commit, operating system and version, architecture, runner type, CPU information when available, memory information when available, Node, PostgreSQL and Docker versions, exact tool names/versions, UTC timestamp, dependency/cache condition, pilot/final classification, and success/failure. GitHub Actions metadata should be captured automatically where practical, including runner OS/architecture, workflow/run IDs, attempt, repository, event, runner name/type, and relevant image label.

## Cache policy

Initial final runs will use **controlled warm-cache conditions**. A standardized priming procedure will populate declared dependency and Docker layers before timing; cache keys, priming outcome, and cache-hit indicators will be recorded. Warm caches reduce uncontrolled network/download variation and better isolate incremental pipeline work while keeping total execution practical. Tool databases that require updates must be pinned or prepared consistently outside the measured boundary, with provenance recorded.

Uncontrolled cache states must never be mixed. If cold-cache behavior is later studied, it becomes a separate, labeled experimental condition with its own protocol version or amendment and analysis stratum.

## Detection and gating policy

Detection is separate from gating. Each scanner should execute, save raw findings, record its native exit/result, and permit subsequent measurement stages to continue where safely possible. Scanner non-zero exit codes are captured rather than allowed to censor later controls. After all required stages, a final experimental gate records whether that configuration would have failed under its frozen policy. Infrastructure is never applied, and unsafe runtime continuation is not required merely to preserve measurement.

## Pilot phase and final repetitions

The initial engineering pilot comprises 5 runs for each of 7 configurations: 35 runs total. Its objectives are to validate instrumentation, identify pipeline failures, measure timing variance, assess cache behavior, verify resource measurement, ensure scanner outputs can be normalized, and estimate variance for final repetition planning. Five is an engineering pilot count, not the final sample size. Pilot outputs remain under `data/raw/pilot/` and are excluded from final estimates.

The final repetition count will be chosen after the pilot using observed variance, effect sizes of practical interest, statistical power/precision considerations, and computational feasibility. The decision and rationale must be recorded before final collection begins; this protocol does not hard-code 30 or 50 runs.

## Preliminary threats to validity

- **Internal validity:** cache state, runner variation, network variation, tool initialization, dependency downloads, and service startup can alter timing. Mitigations include the fixed cache policy, pinned artifacts, consistent boundaries, randomized or balanced configuration order where feasible, run metadata, readiness checks, and pilot-based instrumentation review.
- **Construct validity:** normalization, seeded-vulnerability mapping, tool rule coverage, alert duplication, and severity scales can distort detection measures. Mitigations include frozen schemas/rules, retained raw reports, explicit relevant-scope sets, documented manual adjudication, and separate tool-native versus normalized severity.
- **External validity:** one application, corpus, set of scanner implementations, control ordering, and CI environment limit generalization. Report conclusions at that scope and frame broader claims as future replication questions.
- **Conclusion validity:** repetition count, runtime variance, statistical assumptions, missing runs, and overlapping control detections can affect inference. Use pilot-informed repetitions, report uncertainty/effect sizes, test assumptions, correct multiple comparisons, preserve failures, and avoid treating ordered marginal gain as intrinsic tool value.

## Data governance

Raw outputs are append-only research evidence. Pilot and final namespaces remain separate. Records must validate against `data/schema/run.schema.json`; normalized finding objects validate against `data/schema/finding.schema.json`. No experimental results are included in this protocol commit.
