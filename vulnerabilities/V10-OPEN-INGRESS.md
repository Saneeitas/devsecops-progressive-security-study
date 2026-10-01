# V10 — Open Sensitive Ingress

- **ID:** V10
- **Name:** SSH open to the internet
- **Security layer:** Infrastructure as code/network access
- **Mapping:** CWE-284; OWASP Top 10 A05:2021 Security Misconfiguration
- **Proposed location:** Future `infrastructure/terraform/experimental/v10-open-ingress.tf`
- **Secure baseline behavior:** `infrastructure/terraform/security-group.tf` permits TCP port 22 only from validated `var.admin_cidr`, whose documented default is `10.0.0.0/24` and explicitly rejects `0.0.0.0/0`.
- **Proposed controlled mutation:** Replace the restricted CIDR with `0.0.0.0/0` and remove or bypass the protective variable validation.
- **Why selected:** Sensitive administrative ingress from every IPv4 address is a canonical but realistic cloud misconfiguration with an unambiguous oracle.
- **Expected security-control category:** IaC static analysis and cloud network policy.
- **Potential scanner classes:** Terraform scanners, policy-as-code, CSPM rules, and configuration review.
- **Ground-truth validation:** Parse the Terraform and assert the tuple `{protocol="tcp", from_port=22, to_port=22, cidr="0.0.0.0/0"}`. Do not apply it.
- **Expected detection behavior:** Most IaC scanners should identify world-open SSH. A scanner limited to deployed resources or IPv6-only checks may behave differently.
- **Safety considerations:** Static fixture only; no AWS credentials or resource attachment; CI must prohibit apply.
- **Restoration procedure:** Delete the fixture or restrict ingress to a documented private/admin CIDR, then rerun static validation.
