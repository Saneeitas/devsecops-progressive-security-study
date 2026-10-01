# V06 — Vulnerable Dependency

- **ID:** V06
- **Name:** Known-vulnerable lodash release
- **Security layer:** Software supply chain
- **Mapping:** CVE-2021-23337; CWE-77; OWASP Top 10 A06:2021 Vulnerable and Outdated Components
- **Proposed location:** `application/package.json` and `application/package-lock.json`
- **Secure baseline behavior:** `lodash` is not a direct dependency and the current npm audit is clean.
- **Proposed controlled mutation:** Add exact version `lodash@4.17.20` as an otherwise unused direct dependency. Do not execute its vulnerable template behavior.
- **Why selected:** The affected range is stable and well documented: NVD identifies lodash versions before 4.17.21 as affected by CVE-2021-23337. An unused package allows SCA evaluation without active exploitation.
- **Expected security-control category:** Software composition analysis.
- **Potential scanner classes:** Lockfile SCA, package-manager audit, SBOM scanners, and container package inventory.
- **Ground-truth validation:** Confirm `npm ls lodash` resolves exactly 4.17.20 and compare scanner output with [NVD CVE-2021-23337](https://nvd.nist.gov/vuln/detail/CVE-2021-23337). No exploit is required.
- **Expected detection behavior:** Mature SCA should report CVE-2021-23337 and recommend 4.17.21 or later. Other valid lodash advisories are non-seeded valid findings unless separately added to the manifest.
- **Safety considerations:** Keep the package unused, pin the exact version, use only the isolated branch, and prevent publication/deployment.
- **Restoration procedure:** Remove lodash, regenerate the lockfile with the baseline toolchain, run `npm ls`, tests, build, and dependency audit, and verify the CVE is absent.
