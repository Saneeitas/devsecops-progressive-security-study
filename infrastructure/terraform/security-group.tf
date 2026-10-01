resource "aws_security_group" "restricted_admin" {
  name        = "devsecops-secure-baseline-admin"
  description = "V10 experimental fixture exposing administrative access publicly"
  vpc_id      = var.vpc_id

  ingress {
    description = "V10 SSH open to all IPv4 addresses"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = [var.admin_cidr]
  }
}
