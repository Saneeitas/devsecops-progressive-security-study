# V11 — Overly Permissive IAM

- **ID:** V11
- **Name:** Wildcard IAM actions and resources
- **Security layer:** Infrastructure as code/identity authorization
- **Mapping:** CWE-732; OWASP Top 10 A01:2021 Broken Access Control
- **Proposed location:** Future `infrastructure/terraform/experimental/v11-permissive-iam.tf`
- **Secure baseline behavior:** `infrastructure/terraform/iam.tf` permits only `s3:GetObject` on the fixture bucket's `products/*` objects.
- **Proposed controlled mutation:** Replace the scoped action and resource with `Action = ["*"]` and `Resource = ["*"]`.
- **Why selected:** The policy clearly violates least privilege and exercises semantic IAM analysis rather than simple credential matching.
- **Expected security-control category:** IaC static analysis and IAM policy analysis.
- **Potential scanner classes:** Terraform scanners, policy-as-code, IAM access analyzers, and manual review.
- **Ground-truth validation:** Render/inspect the policy JSON offline and assert that both action and resource are global wildcards. Do not create or attach the policy.
- **Expected detection behavior:** IaC tools should report administrative wildcard privileges, though severity and duplicate findings may vary.
- **Safety considerations:** No provider credentials, apply, principal attachment, or real account identifiers.
- **Restoration procedure:** Remove the fixture or replace wildcards with the minimum explicit actions and scoped resource ARNs, then rerun policy analysis.
