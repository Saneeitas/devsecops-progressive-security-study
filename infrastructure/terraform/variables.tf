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
  description = "Restricted private CIDR permitted to reach the SSH fixture."
  type        = string
  default     = "10.0.0.0/24"

  validation {
    condition     = can(cidrnetmask(var.admin_cidr)) && var.admin_cidr != "0.0.0.0/0"
    error_message = "admin_cidr must be a valid restricted IPv4 CIDR and cannot be 0.0.0.0/0."
  }
}

variable "availability_zone" {
  description = "Availability zone for the encrypted EBS fixture."
  type        = string
  default     = "us-east-1a"
}
