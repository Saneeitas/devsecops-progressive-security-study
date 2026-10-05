# Security Tool Treatment Specifications v1

## Status and scope

This is a pre-result specification for `corpus-v1` (`eeb2e772ffb60fb214df8b41866be23be89dcf3f`). Commands below are future invocation patterns and have not been executed. Each tool is restricted to its assigned control role. Tool binaries/images, rule bundles, advisory databases, and scan configuration must be frozen before the pilot and recorded in every run.

## Version snapshot

| Configuration | Control | Tool | Version/tag | Release date | Intended distribution |
|---|---|---|---|---|---|
| C1 | SAST | Semgrep | `1.178.0` / `v1.178.0` | 2026-09-23 | Official image index `sha256:32e459…42786b`; Linux/amd64 manifest `sha256:fbba1f…66ffb` |
| C2 | SCA | OSV-Scanner | `2.6.0` / `v2.6.0` | 2026-09-14 | Official GitHub release binary and checksum |
| C3 | Secrets | Gitleaks | `8.30.1` / `v8.30.1` | 2026-03-21 | Official GitHub release binary and checksum |
| C4 | Container vulnerabilities | Trivy | `0.74.0` / `v0.74.0` | 2026-08-14 | Official image index `sha256:62b1e6…7c1969`; Linux/amd64 manifest `sha256:ee940a…3c5c9` |
| C5 | Terraform IaC | Checkov | `3.3.8` / `3.3.8` | 2026-07-09 | Exact PyPI package in an isolated, frozen tool environment |
| C6 | DAST | OWASP ZAP | `2.17.0` / `v2.17.0` | 2025-12-15 | Official image index `sha256:781a2b…081ef`; Linux/amd64 manifest `sha256:71db37…84efa` |

Official release provenance and verification commands are machine-readable in `tool-versions.json`. The frozen Semgrep rules, OSV/Trivy advisory data, and ZAP add-on inventory are recorded in `research/experiment-artifacts-v1.json`.

## C1: Semgrep SAST

**Boundary.** Scan only `application/src/**/*.ts`. Exclude `application/dist`, `node_modules`, coverage, tests, `research`, `data`, `vulnerabilities`, Docker/Compose, Terraform, lockfiles, and generated files. This excludes dependency, secret, container, and IaC analysis.

**Rules.** Use the 177 JavaScript/TypeScript security YAML files selected by `pipeline/security/semgrep-rules-v1.json` from Semgrep Community Edition rules revision `a84ff9cc2453ca91d581380de4b8b3f272f6f4be`. Verify the source archive and selected-file composite checksum stated there, materialize that local bundle before timing, and use it for every run. Do not use `--config auto`, Semgrep Secrets, Semgrep Supply Chain, `semgrep ci`, managed policies, or network-fetched rules during measured runs.

**Future invocation pattern (not executed):**

```sh
semgrep scan \
  --config pipeline/security/semgrep-rules-v1/ \
  --json --output artifacts/semgrep.json \
  --error \
  --exclude 'application/tests/**' \
  --exclude 'application/dist/**' \
  --exclude 'application/node_modules/**' \
  application/src
```

JSON is the raw output. Capture Semgrep's native exit code before a wrapper continues: normally 0 without findings and, with `--error`, nonzero when findings meet the tool's error behavior; execution/configuration errors remain distinct. Derive the experimental gate afterward from normalized findings. Verify with `semgrep --version` and require `1.178.0`.

## C2: OSV-Scanner SCA

**Boundary.** Scan only the resolved Node lockfile `application/package-lock.json` using lockfile mode. Do not scan source directories, the container image, installed `node_modules`, SBOMs, Git history, or invoke remediation. The package manifest is contextual; the lockfile is the authoritative target.

**Future invocation pattern (not executed):**

```sh
osv-scanner scan source \
  --lockfile application/package-lock.json \
  --format json \
  --output-file artifacts/osv-scanner.json
```

JSON is the raw output. Native exit 0 means no known findings, 1 means findings, 127 is a general error, and 128 means no packages found; preserve it and continue via the orchestration wrapper. Freeze the OSV database snapshot or query response provenance before the pilot so all configurations/runs use the same advisory state. Verify with `osv-scanner --version` and require `2.6.0`.

## C3: Gitleaks secret scanning

**Boundary.** Use filesystem/current-tree scanning with `gitleaks dir`, rooted at the checked-out repository. Do not scan Git history, commits, reflogs, or remote branches. Exclude `.git/`, `data/raw/`, generated artifacts, `application/node_modules/`, and `application/dist/`. This ensures the treatment evaluates the exact corpus snapshot without historical baseline/protocol content creating unrelated observations.

Use the default rules embedded in Gitleaks 8.30.1 plus a frozen experiment configuration containing only path exclusions and no allowlist for the seeded fixture. Record that configuration's checksum.

**Future invocation pattern (not executed):**

```sh
gitleaks dir . \
  --config pipeline/security/gitleaks.toml \
  --report-format json \
  --report-path artifacts/gitleaks.json \
  --exit-code 1 \
  --no-banner
```

Preserve native exit 1 for findings and distinguish execution errors; the wrapper continues. JSON is the raw output. Verify with `gitleaks version` and require `8.30.1`.

## C4: Trivy container vulnerability scanning

**Boundary.** Scan the locally built experimental API image identified by immutable image ID/digest. Invoke only the `vuln` scanner. Explicitly do not invoke secret, misconfiguration/IaC, license, SBOM generation, repository, filesystem, Kubernetes, or source scanners. `V08` container-user configuration is therefore outside this C4 treatment.

Scan every severity (`UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL`) and include fixed and unfixed vulnerabilities; do not use an ignore file or VEX suppression in v1. Freeze and checksum the vulnerability database artifact before pilot runs, use it offline during measured runs, and record its update timestamp/digest.

**Future invocation pattern (not executed):**

```sh
trivy image \
  --scanners vuln \
  --format json --output artifacts/trivy.json \
  --severity UNKNOWN,LOW,MEDIUM,HIGH,CRITICAL \
  --ignore-unfixed=false \
  --skip-db-update --skip-java-db-update \
  --exit-code 1 \
  devsecops-corpus@sha256:<BUILT_IMAGE_DIGEST>
```

Capture the native finding exit code and continue. Database/setup failures are execution errors, not findings. Verify with `trivy --version` and require `0.74.0` plus the frozen database metadata.

## C5: Checkov Terraform IaC scanning

**Boundary.** Scan only `infrastructure/terraform/` with `--framework terraform`. Do not scan Dockerfiles, workflows, Kubernetes, secrets, packages, container images, OpenAPI, or application files. Use Checkov's built-in Terraform policies for version 3.3.8 without external policies, platform/API keys, suppressions, or skipped checks. `--skip-download` prevents platform policy/data changes. `BC_API_KEY`, `PRISMA_API_URL`, `CKV_CHECK`, `CKV_SKIP_CHECK`, and `CKV_FRAMEWORK` must be unset; no external checks directory is configured.

**Future invocation pattern (not executed):**

```sh
checkov \
  --directory infrastructure/terraform \
  --framework terraform \
  --output json \
  --output-file-path artifacts/checkov.json \
  --skip-download \
  --soft-fail
```

No checks are skipped. JSON is the raw output. `--soft-fail` makes detection non-blocking; retain finding counts and any execution diagnostics, then compute the conceptual gate separately. Verify with `checkov --version` and require `3.3.8`.

## C6: OWASP ZAP API DAST

**Selected mode.** Use the documented ZAP API Scan in OpenAPI mode, with active and passive API-oriented rules. This is preferable to Baseline Scan because baseline is passive and cannot adequately exercise injection paths. It is preferable to generic Full Scan because the application is a JSON REST API without a navigable frontend; API Scan imports a defined endpoint surface and tunes active scanning for APIs.

**Target and definition.** Target only the isolated Compose API at `http://api:3000`. Before the pilot, create and freeze a pipeline-only OpenAPI 3 definition describing `/api/health`, `/api/health/db`, authentication, users, products/search, orders, and admin diagnostics/products/users/orders. Its checksum becomes an invariant. The API definition must not change application behavior and must set the server to the isolated target. No external URL is allowed.

**Authentication.** A pre-scan setup step creates disposable normal-user/admin fixture data through the existing seed process, logs in through `/api/auth/login`, and injects the resulting bearer JWT through a frozen ZAP context/replacer configuration. Tokens are ephemeral, redacted from artifacts, and never committed. Run one authenticated context plus public endpoints. Standard API Scan is not a multi-principal authorization harness; consequently V04 detection is possible in theory but not reasonably expected from this treatment without a separately specified two-session script, which v1 does not add.

**Future invocation pattern (not executed):**

```sh
zap-api-scan.py \
  -t /zap/wrk/pipeline/security/openapi-corpus-v1.yaml \
  -f openapi \
  -n /zap/wrk/pipeline/security/zap-context.context \
  -U corpus-admin \
  -c /zap/wrk/pipeline/security/zap-rules.conf \
  -J /zap/wrk/artifacts/zap.json \
  -T 15
```

The outer pipeline enforces a **30-minute total ZAP timeout**, including import, authentication, passive processing, and active scan. Do not enable alpha rules (`-a`) in v1. Freeze installed add-on versions and the rule configuration; default rules are recorded as `WARN`, with the conceptual gate derived later. ZAP API Scan exits 0 for success, 1 for at least one configured FAIL, 2 for WARN without FAIL, and 3 for operational failure. Capture that code and continue safely. Verify the container with `zap.sh -version` and require core `2.17.0`.

## Detection and gating normalization

Every tool produces two conceptual outputs:

1. **Detection result:** immutable raw JSON, native exit code, execution status, normalized findings, and V01–V12 mapping.
2. **Gate result:** a derived `PASS`, `FAIL`, or `ERROR` under the frozen threshold policy after all required controls have executed.

The orchestration layer will temporarily disable fail-fast behavior around each scanner, record start/end time and native status, validate/persist output, and then continue to the next control when safe. It must never convert a tool execution error into “no findings.” The final experimental gate is evaluated only after all configured stages complete, preventing earlier detections from censoring later measurements.

## Reproducibility artifacts

Container manifests, Semgrep rule selection, Gitleaks/Checkov configuration, OSV identity metadata, Trivy database artifact, OpenAPI contract, DAST dataset, DAST contract, and the ZAP add-on inventory are recorded in `research/experiment-artifacts-v1.json`. The inventory was obtained with `zap.sh -cmd -addonlist` from the pinned Linux/amd64 image while Docker networking was disabled and no target was supplied. No `-addonupdate` or add-on installation is allowed.

## Limitations

One selected implementation represents each control category. Rule/configuration choices directly affect detection. Versions and advisory/rule snapshots are a fixed temporal view. Findings cannot automatically generalize to every SAST, SCA, secret, container, IaC, or DAST tool. Several tools can perform multiple roles; those capabilities are deliberately disabled or not invoked to preserve treatment isolation. This constraint can reduce real-world coverage and is part of the experimental construct.

## Official references

- Semgrep releases and community rules: <https://github.com/semgrep/semgrep/releases/tag/v1.178.0>, <https://github.com/semgrep/semgrep-rules>
- OSV-Scanner release, usage, output, and supported lockfiles: <https://github.com/google/osv-scanner/releases/tag/v2.6.0>, <https://google.github.io/osv-scanner/usage/>, <https://google.github.io/osv-scanner/output/>, <https://google.github.io/osv-scanner/supported-languages-and-lockfiles/>
- Gitleaks release: <https://github.com/gitleaks/gitleaks/releases/tag/v8.30.1>
- Trivy release and installation guidance: <https://github.com/aquasecurity/trivy/releases/tag/v0.74.0>, <https://trivy.dev/latest/getting-started/installation/>
- Checkov release and CLI behavior: <https://github.com/bridgecrewio/checkov/releases/tag/3.3.8>, <https://www.checkov.io/2.Basics/CLI%20Command%20Reference.html>
- ZAP release and API Scan behavior: <https://www.zaproxy.org/blog/2025-12-15-zap-2-17-0/>, <https://www.zaproxy.org/docs/docker/api-scan/>
