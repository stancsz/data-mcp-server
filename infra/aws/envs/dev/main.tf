# Minimal Terraform root for AWS dev environment (placeholder)
# Backend configuration should be added in backend.tf or via CLI/environment variables.
#
# Example backend (uncomment and edit before use):
# terraform {
#   backend "s3" {
#     bucket         = "my-terraform-state-bucket"
#     key            = "data-mcp/aws/dev/terraform.tfstate"
#     region         = "us-central-1"
#     dynamodb_table = "mcp-terraform-locks"
#     encrypt        = true
#   }
# }

terraform {
  required_version = ">= 1.0.0"
}

# Provider block is intentionally minimal / commented. Operators should supply proper credentials.
# provider "aws" {
#   region = var.region
# }

variable "region" {
  type    = string
  default = "us-west-2"
  description = "AWS region for resources"
}

# Example resource placeholder (no-op). Replace with real modules/resources.
resource "null_resource" "placeholder" {
  provisioner "local-exec" {
    command = "echo infra/aws/envs/dev placeholder"
  }
}

output "placeholder" {
  value = "infra/aws/envs/dev configured"
}
