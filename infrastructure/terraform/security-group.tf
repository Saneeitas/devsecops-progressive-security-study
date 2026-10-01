resource "aws_security_group" "restricted_admin" {
  name        = "devsecops-secure-baseline-admin"
  description = "Secure fixture permitting administrative access only from a restricted CIDR"
  vpc_id      = var.vpc_id

  ingress {
    description = "SSH from the documented administrative network"
    protocol    = "tcp"
    from_port   = 22
    to_port     = 22
    cidr_blocks = [var.admin_cidr]
  }
}
