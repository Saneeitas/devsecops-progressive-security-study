# V07 — Vulnerable Container Component

- **ID:** V07
- **Name:** Node runtime containing a known fixed vulnerability
- **Security layer:** Container/software component
- **Mapping:** CVE-2023-30581
- **Proposed location:** Both `FROM` lines in `application/Dockerfile`
- **Secure baseline behavior:** The image uses Node 22 on Alpine 3.22 and currently builds with a clean npm dependency audit.
- **Proposed controlled mutation:** On the isolated V07 branch, replace the Node base with `node:18.16.0-bullseye-slim`, pin its immutable digest at injection time, and record the resolved OS packages and scanner database date. Node 18.16.1 lists CVE-2023-30581 among its fixed issues.
- **Why selected:** A fixed historical Node runtime CVE gives a concrete application-runtime component for container scanning without requiring exploitation.
- **Expected security-control category:** Container image scanning and SBOM analysis.
- **Potential scanner classes:** OS/runtime image scanners, registry scanners, SBOM-to-advisory matching, and policy gates.
- **Ground-truth validation:** Record `node --version` as 18.16.0, image digest, package inventory, and a scanner report for CVE-2023-30581. Do not exercise the policy-bypass vulnerability.
- **Expected detection behavior:** Scanner coverage varies: some tools inventory the Node binary, while OS-package-only scanners may miss it. Other genuine findings in the old Debian image are non-seeded valid findings.
- **Safety considerations:** No deployment, no exploit, no registry promotion, no production credentials, and retain the immutable digest because tag contents and advisory databases change.
- **Restoration procedure:** Restore both Node 22 Alpine base lines and digest policy from the baseline, rebuild without cache, confirm Node 22, and rescan.
