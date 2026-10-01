# V12 — Missing Encryption

- **ID:** V12
- **Name:** Unencrypted EBS volume
- **Security layer:** Infrastructure as code/data protection
- **Mapping:** CWE-311; OWASP Top 10 A02:2021 Cryptographic Failures
- **Proposed location:** Future `infrastructure/terraform/experimental/v12-unencrypted-ebs.tf`
- **Secure baseline behavior:** `infrastructure/terraform/ebs.tf` defines the static EBS fixture with `encrypted = true`.
- **Proposed controlled mutation:** Change only the fixture's encryption property to `encrypted = false`. It must remain unattached and unapplied.
- **Why selected:** Explicitly disabled at-rest encryption is straightforward ground truth and avoids overlap with the public-access semantics of V09.
- **Expected security-control category:** IaC static analysis and cloud data-protection policy.
- **Potential scanner classes:** Terraform scanners, policy-as-code, CSPM rules, and configuration review.
- **Ground-truth validation:** Parse the Terraform and assert that the EBS resource explicitly sets `encrypted` to `false`. Do not run `terraform apply`.
- **Expected detection behavior:** IaC tools should report missing EBS encryption. Tools that depend only on account-level default encryption may classify it differently; record that context.
- **Safety considerations:** Static fixture only; no cloud credentials, apply, attachment, or data.
- **Restoration procedure:** Remove the fixture or set `encrypted = true` and specify an approved KMS key policy, then rerun static validation.
