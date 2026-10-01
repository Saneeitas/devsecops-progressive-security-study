variable "aws_region" {
  description = "AWS region used only if these fixtures are later adapted for an approved deployment."
  type        = string
  default     = "us-east-1"
}

variable "vpc_id" {
  description = "VPC identifier for the security-group fixture."
  type        = string
  default     = "vpc-00000000000000000"
}

variable "admin_cidr" {
  description = "V10 experimental CIDR that intentionally exposes SSH publicly."
  type        = string
  default     = "0.0.0.0/0"
}

variable "availability_zone" {
  description = "Availability zone for the encrypted EBS fixture."
  type        = string
  default     = "us-east-1a"
}
