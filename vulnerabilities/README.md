# Controlled Vulnerability Corpus Design

This directory defines the ground truth for the progressive security-control experiment. Every entry is **designed only**. No vulnerability in this corpus has been injected into the secure baseline.

The corpus represents realistic weaknesses across application source, API authorization, secrets, software dependencies, containers, and infrastructure as code. Selection is based on architectural relevance and experimental coverage rather than guaranteed scanner detection. A missed seeded weakness is a valid result.

## Corpus

| ID | Selected weakness | Layer | Primary mapping | Planned location | Expected controls |
|---|---|---|---|---|---|
| V01 | SQL injection | Application source | CWE-89 | `application/src/services/product.service.ts` | SAST, DAST |
| V02 | OS command injection | Application source | CWE-78 | Future admin diagnostics route/service | SAST, DAST |
| V03 | Mass assignment of user role | API/property authorization | CWE-915, OWASP API3:2023 | Registration controller/service | SAST, API/DAST, tests |
| V04 | Broken object level authorization | API authorization | CWE-639, OWASP API1:2023 | `getOrder` in order service | SAST, API/DAST, tests |
| V05 | Hardcoded fake secret | Source/secrets | CWE-798 | Future research fixture/config file | Secret scanning |
| V06 | Vulnerable lodash dependency | Software supply chain | CVE-2021-23337 | `application/package.json` and lockfile | SCA |
| V07 | Vulnerable Node base image | Container component | CVE-2023-30581 | `application/Dockerfile` base image | Container scanning |
| V08 | Container running as root | Container configuration | CWE-250 | `application/Dockerfile` runtime stage | Dockerfile/IaC scanning |
| V09 | Public S3 configuration | IaC | CWE-284, CWE-732 | `infrastructure/terraform/s3.tf` | IaC scanning |
| V10 | Open SSH ingress | IaC | CWE-284 | `infrastructure/terraform/security-group.tf` | IaC scanning |
| V11 | Wildcard IAM permissions | IaC | CWE-732 | `infrastructure/terraform/iam.tf` | IaC scanning |
| V12 | Unencrypted EBS volume | IaC | CWE-311 | `infrastructure/terraform/ebs.tf` | IaC scanning |

## V03 selection decision

Reflected XSS was rejected. The application returns JSON and has no browser-rendered frontend or HTML response sink, so merely reflecting a string in JSON would not create a credible executable-script condition. V03 instead models mass assignment: a later experimental mutation would allow registration input to set the protected `role` property. This directly fits the API architecture and maps to [CWE-915](https://cwe.mitre.org/data/definitions/915) and [OWASP API3:2023 Broken Object Property Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa3-broken-object-property-level-authorization/).

## V08 baseline prerequisite resolved

Secure baseline v2 configures the official image's unprivileged `node` user and copies runtime files with that ownership. The future V08 mutation will remove the `USER node` instruction so the experimental runtime executes as UID 0.

## Other baseline and reproducibility observations

- The Node and PostgreSQL image references are tags rather than immutable digests. Resolve and record digests for each experimental run so later registry changes do not change the scanned artifact.
- Secure Terraform counterparts now exist for V09–V12. Each future mutation must change only its corresponding secure property.
- Role authorization trusts the signed JWT role until token expiry. A database-side role revocation is therefore not immediate. This is outside the seeded corpus and should be retained as a possible non-seeded valid finding if a control reports it.

## Ground-truth classification

Each normalized tool finding must be evaluated against the corpus, the mutated commit, its exact location, and the relevant data-flow or configuration semantics:

1. **Seeded True Positive** — the finding correctly identifies an injected corpus item, its vulnerable location, and the intended weakness or equivalent root cause.
2. **Seeded False Negative** — an injected corpus item is present and validated by its canary/oracle, but the control produces no qualifying finding for it.
3. **Non-seeded Valid Finding** — the finding identifies a real weakness that is not the intended seed. This includes extra CVEs in an intentionally old package or image and pre-existing baseline defects.
4. **False Positive** — the reported weakness is absent, unreachable under the defined model, points to a non-vulnerable construct, or cannot be confirmed by review and the documented oracle.

Findings are matched by root cause and location, not message text alone. Ambiguous findings receive manual adjudication with the tool output, source snapshot, configuration, dependency graph, scanner database version, and validation evidence retained. Duplicate reports from one tool are consolidated before calculating detection metrics.

## Experiment controls and safety

- Create one mutation commit or branch per vulnerability and record its parent baseline commit.
- Run only in disposable local/CI environments with synthetic data and no cloud credentials.
- Never deploy the Terraform vulnerability fixtures; static parsing/planning is sufficient.
- Use benign canaries for SQL, command, authorization, and secret validation.
- Record scanner name/version, rules/database version, configuration, timestamps, and raw output.
- Restore by reverting the mutation commit or checking out the recorded secure baseline; verify tests and the vulnerability-specific negative oracle afterward.

## Reference anchors

- [MITRE CWE-89: SQL Injection](https://cwe.mitre.org/data/definitions/89.html)
- [MITRE CWE-78: OS Command Injection](https://cwe.mitre.org/data/definitions/78.html)
- [OWASP API1:2023 Broken Object Level Authorization](https://api-security.owasp.org/editions/2023/en/0xa1-broken-object-level-authorization/)
- [NVD CVE-2021-23337](https://nvd.nist.gov/vuln/detail/CVE-2021-23337)
- [Node.js 18.16.1 security release](https://github.com/nodejs/node/blob/main/doc/changelogs/CHANGELOG_V18.md#2023-06-20-version-18161-hydrogen-lts-rafaelgss)
