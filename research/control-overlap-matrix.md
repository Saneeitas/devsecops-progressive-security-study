# Security-control overlap and treatment isolation

Capability labels describe what a tool family can potentially do, not what this experiment invokes.

| Tool | SAST | SCA | Secrets | Container | IaC | DAST |
|---|---|---|---|---|---|---|
| Semgrep | **Enabled** | Available, disabled | Available, disabled | Not invoked | Available via rules, excluded | No |
| OSV-Scanner | No | **Enabled** | No | Available, disabled | No | No |
| Gitleaks | No | No | **Enabled** | No | No | No |
| Trivy | No | Available via filesystem/repository, disabled | Available, disabled | **Enabled: vulnerabilities only** | Available, disabled | No |
| Checkov | No | Available, disabled | Available, disabled | Available, disabled | **Enabled: Terraform only** | No |
| OWASP ZAP | No | No | No | No | No | **Enabled: API active/passive scan** |

## Isolation decisions

- Semgrep scans only TypeScript under `application/src` with a frozen SAST rules bundle. Semgrep Secrets, Supply Chain, Dockerfile, Terraform, and managed CI capabilities are not invoked.
- OSV-Scanner receives only `application/package-lock.json`; its container-image and broad source discovery modes are not invoked.
- Gitleaks uses current-tree filesystem mode. Git history is excluded.
- Trivy receives only the built image with `--scanners vuln`. Secret, misconfiguration/IaC, filesystem, repository, license, and SBOM modes are not invoked.
- Checkov uses only `--framework terraform` on `infrastructure/terraform/`. Its secrets, SCA, image, Dockerfile, workflow, and OpenAPI frameworks are excluded.
- ZAP uses API Scan against the isolated running service. It does not analyze source, dependencies, images, secrets, or Terraform.

Overlap remains possible at the finding level: Semgrep and ZAP may both observe injection classes; OSV-Scanner and Trivy may both identify a vulnerable application package if that package exists in the final image. Such overlap is retained and attributed to each detecting control. Ordered marginal gain records only new cumulative coverage and is not interpreted as intrinsic category value.

`V08` is intentionally outside the configured Trivy vulnerability-only treatment and the Terraform-only Checkov treatment. This exposes a corpus-to-treatment coverage limitation rather than justifying cross-role capability enablement after results are observed.
