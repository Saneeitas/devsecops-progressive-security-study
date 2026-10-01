# Secure Terraform Baseline Fixtures

These minimal AWS resources are static experimental controls for future V09–V12 mutations. They are not deployment infrastructure and must not be applied during baseline or scanner experiments.

- S3 blocks all public access, enforces bucket-owner ownership, and uses server-side encryption.
- The security group permits SSH only from the documented `admin_cidr`, whose default is a private documentation fixture CIDR.
- IAM permits only `s3:GetObject` for objects in the fixture bucket.
- The EBS fixture explicitly enables encryption.

Static verification:

```bash
terraform init -backend=false
terraform fmt -check
terraform validate
```

Do not run `terraform apply`. A real deployment would also need organization-specific naming, network IDs, KMS policy, logging, lifecycle, and tagging controls.
