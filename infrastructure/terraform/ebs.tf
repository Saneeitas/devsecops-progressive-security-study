resource "aws_ebs_volume" "encrypted_fixture" {
  availability_zone = var.availability_zone
  size              = 1
  type              = "gp3"
  # V12: encryption is intentionally disabled for static IaC research.
  encrypted = false
}
