# V09 — Public S3 Configuration

- **ID:** V09
- **Name:** Publicly readable S3 bucket
- **Security layer:** Infrastructure as code
- **Mapping:** CWE-284, CWE-732; OWASP Top 10 A01:2021 Broken Access Control
- **Proposed location:** Future `infrastructure/terraform/experimental/v09-public-s3.tf`
- **Secure baseline behavior:** `infrastructure/terraform/s3.tf` blocks all four forms of public access, enforces bucket-owner ownership, has no public policy/ACL, and enables AES-256 server-side encryption.
- **Proposed controlled mutation:** Change the baseline public-access-block settings to permit public policy behavior and add a bucket policy granting `s3:GetObject` to principal `*`.
- **Why selected:** Public object storage is a realistic, statically detectable cloud access-control error with no need to provision infrastructure.
- **Expected security-control category:** IaC static analysis and cloud-policy review.
- **Potential scanner classes:** Terraform/IaC scanners, policy-as-code, cloud security posture rules, and manual policy review.
- **Ground-truth validation:** Run offline Terraform parsing/validation and assert that the effective policy has principal `*` and public-access blocking is disabled. Do not run `terraform apply`.
- **Expected detection behavior:** IaC tools should report public S3 access; rule names and whether policy plus block settings produce one or multiple findings will vary.
- **Safety considerations:** No backend credentials, provider authentication, apply, import, or real bucket. Deny deployment in CI.
- **Restoration procedure:** Remove the experimental resource or restore all four public-access-block flags and eliminate public principals; validate the static plan/configuration again.
