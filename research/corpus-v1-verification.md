# Corpus v1 ground-truth verification

- **Secure baseline:** `secure-baseline-v2` / `7067c5b2bf862893056959b0c15cd04d15cf183f`
- **Experimental branch:** `experiment/vulnerability-corpus-v1`
- **Experimental commit:** pending; verification was performed against the current working tree before commit
- **Verification date:** 2026-10-01
- **Scope:** controlled local research environment; no security scanner was run and no Terraform resource was deployed

## Results

| ID | Mutation location | Secure baseline behavior | Experimental behavior | Verification and result | Expected control | Mapping |
|---|---|---|---|---|---|---|
| V01 | `application/src/services/product.service.ts` | Product search binds the query as `$1`. | Search input is interpolated into SQL. | Ground-truth test submits a quote-bearing expression and observes broadened results: **passed**. | SAST, DAST | CWE-89; OWASP A03:2021 |
| V02 | `application/src/services/diagnostics.service.ts`; `GET /api/admin/diagnostics/ping` | No command-execution endpoint exists. | An admin-only diagnostic passes its bounded research input to an interpolated `exec` command. | Test confirms anonymous rejection and observes the harmless `V02_CANARY` output as admin: **passed**. | SAST, DAST | CWE-78; OWASP A03:2021 |
| V03 | `auth.controller.ts`; `auth.service.ts` | Registration fixes the role to `user`. | Registration accepts and persists a client-supplied role. | Test registers with `role=admin` and accesses an admin endpoint: **passed**. | SAST, API/DAST | CWE-915; OWASP API3:2023 |
| V04 | `application/src/services/order.service.ts` | Order lookup scopes by order ID and authenticated user ID. | Lookup scopes only by order ID while authentication remains required. | Anonymous request returns 401; User A retrieves User B's order: **passed**. | API/DAST, SAST | CWE-639, CWE-862; OWASP API1:2023 |
| V05 | `application/src/config/research-fixture.ts` | No provider-shaped credential fixture exists. | A clearly non-functional `ghp_` research token is committed as source text. | Test confirms the stable fixture and all-zero payload: **passed**. | Secret scanning | CWE-798 |
| V06 | `application/package.json`; `package-lock.json` | No direct vulnerable lodash pin. | Both files deterministically pin `lodash@4.17.20`. | Test reads both manifests and confirms exact versions: **passed**. | SCA | CVE-2021-23337; CWE-77; OWASP A06:2021 |
| V07 | `application/Dockerfile` | Runtime uses current Node 22 Alpine baseline. | Build and runtime use `node:18.16.0-bullseye-slim` at digest `sha256:2b05866efb50b6bbc642e6d1cef908372351ad981453b8a747b1d0c9b5777cd8`. | Source test confirms both pinned `FROM` instructions; image build passed and runtime reports Node 18.16.0: **passed**. | Container scanning, SBOM | CVE-2023-30581; OWASP A06:2021 |
| V08 | `application/Dockerfile` runtime stage | `USER node` runs the service without UID 0. | The runtime stage omits `USER`, retaining the image's root default. | Source test confirms omission; `docker exec ... id -u` returned `0`: **passed**. | IaC/container configuration | CWE-250 |
| V09 | `infrastructure/terraform/s3.tf` | Public access block is enabled and no public policy exists. | Public-access blocks are disabled and a public-read bucket policy is present. | Ground-truth source assertions plus `terraform validate`: **passed**. | IaC analysis | CWE-284, CWE-732; OWASP A01:2021 |
| V10 | `security-group.tf`; `variables.tf` | SSH ingress uses a restricted documented CIDR. | Administrative port 22 permits `0.0.0.0/0`. | Ground-truth source assertion plus `terraform validate`: **passed**. | IaC analysis | CWE-284; OWASP A05:2021 |
| V11 | `infrastructure/terraform/iam.tf` | Policy permits only required S3 reads on the fixture bucket. | Policy uses wildcard action and resource. | Ground-truth source assertions plus `terraform validate`: **passed**. | IaC/IAM analysis | CWE-732; OWASP A01:2021 |
| V12 | `infrastructure/terraform/ebs.tf` | The EBS fixture explicitly enables encryption. | The EBS fixture explicitly sets `encrypted = false`. | Ground-truth source assertion plus `terraform validate`: **passed**. | IaC analysis | CWE-311; OWASP A02:2021 |

## Test interpretation

The dedicated ground-truth suite passed 11/11 tests and covers all twelve mutations. The unchanged functional suite passed 11/12 tests. Its sole failure is the original V04 protection assertion (expected 404, received 200), which is retained as direct evidence of the intentional authorization regression rather than rewritten to accept vulnerable production behavior.

TypeScript compilation, Docker image construction, Compose migration and seed, API health, database health, root-UID verification, `terraform fmt`, and `terraform validate` passed. The older V07 runtime emits package-engine warnings for development tools that target newer Node releases; compilation and the production runtime still complete successfully.
