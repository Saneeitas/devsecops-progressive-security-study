# Statistical Analysis Plan v1

## Scope and analysis populations

This preliminary plan is defined before pilot or final results. The pilot population is used only for instrumentation and final repetition planning. The final population contains eligible final runs executed under the frozen protocol and invariants. Exclusions, retries, timeouts, and missing data must be retained and reported with prespecified reasons; failed runs are not silently discarded.

Security effectiveness and operational performance are distinct outcome types. With a fixed corpus, tool version, configuration, and rule set, vulnerability coverage may be deterministic or nearly deterministic; repeated identical coverage observations do not create independent security evidence. Runtime and resource measures are stochastic and require repeated runs.

## Outcomes

Primary security outcomes are scope-adjusted seeded detection coverage and all-corpus coverage. Secondary security outcomes include vulnerability-level recall, finding-level precision/F1, counts by classification, first-detection configuration, and ordered marginal gain.

Primary operational outcome is total pipeline wall-clock duration. Secondary outcomes include stage/scanner durations, absolute and relative overhead against C0, CPU utilization, peak memory, finding counts, failure rates, and gate outcomes.

## Descriptive analysis

For continuous operational outcomes, report count, mean, median, standard deviation, interquartile range, minimum, maximum, and confidence intervals where appropriate. For categorical outcomes, report counts and proportions with suitable intervals. Coverage and classification counts are reported by configuration, tool, vulnerability, and relevant control scope.

Use plots such as dot/strip plots, boxplots, violin or empirical-distribution plots, run-order plots, and Q-Q plots as appropriate. Inspect distributions, skew, outliers, heteroscedasticity, time trends, and block effects. Normality may be assessed with graphical evidence and tests where informative, but is never assumed automatically or decided from a single test.

## Comparative analysis

Final test selection depends on the execution design and observed distributions:

- If runs are meaningfully paired or blocked across configurations, use repeated-measures or block-aware models.
- The Friedman test is a candidate for non-parametric repeated comparisons, followed by appropriate corrected post-hoc comparisons.
- ANOVA or repeated-measures ANOVA is considered only when independence, residual, variance/covariance, and other relevant assumptions are justified; corrections or mixed models may be preferable.
- If runs are independent rather than paired, use methods matching that design rather than forcing repeated-measures analysis.
- Multiple comparisons require a stated family and correction method chosen before final confirmatory analysis.

Report effect sizes and confidence intervals alongside p-values. Candidate effect sizes include paired/standardized mean differences where assumptions fit, robust or rank-based effects otherwise, and absolute/relative duration differences for practical interpretation. Confidence interval methods must match the estimator and design; bootstrap methods may be used with reproducible seeds when suitable.

## Security-specific analysis

For deterministic coverage, present the complete detection matrix, exact proportions, overlap among controls, first-detection configuration, and marginal gains without pretending repeated runs increase the corpus sample size. If detections vary due to transient execution behavior, quantify that variation per vulnerability and investigate it as reliability evidence.

Recall denominators use only declared in-scope seeded vulnerabilities for control-specific comparisons. All-corpus coverage always uses 12. Findings outside the corpus undergo manual validation and contribute to precision only after deduplication and classification under frozen rules.

## Operational overhead analysis

C0 is the operational reference. Configuration summaries are the primary basis for absolute and relative overhead; arbitrary individual runs are not paired. If a randomized block design is adopted after the pilot, within-block contrasts may be primary. Analyze total duration directly rather than reconstructing it from stage sums. Stage durations explain composition but do not replace total wall time.

## Missingness, failures, and sensitivity

Record all scheduled runs, including startup failures, timeouts, scanner errors, and instrumentation loss. Distinguish pipeline failure from missing measurement. Define retry treatment before final collection. Report complete-case counts and reasons; consider sensitivity analyses that treat timeout durations at their cap or analyze success probability separately. Outlier removal requires a documented technical cause and a sensitivity result with the observation retained.

## Pilot-informed decisions

After the 35 pilot runs, record variance estimates, cache stability, blockability, practical effect sizes, instrumentation completeness, and computational cost. Use these to select and document final repetition count, ordering/randomization, candidate model, interval method, and multiple-comparison family before final data collection. Pilot outcomes are never pooled into final inferential estimates.
