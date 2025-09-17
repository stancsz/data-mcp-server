# Minimal Terraform root for GCP dev environment (placeholder)
# Backend configuration should be added in backend.tf or via CLI/environment variables.
#
# Example backend (uncomment and edit before use):
# terraform {
#   backend "gcs" {
#     bucket = "my-terraform-state-bucket-gcp"
#     prefix = "data-mcp/gcp/dev"
#   }
# }

terraform {
  required_version = ">= 1.0.0"
}

# Provider block is intentionally minimal / commented. Operators should supply proper credentials.
# provider "google" {
#   project = var.project
#   region  = var.region
# }

variable "project" {
  type        = string
  description = "GCP project id"
  default     = "my-gcp-project-dev"
}

variable "region" {
  type        = string
  description = "GCP region"
  default     = "us-central1"
}

# Example resource placeholder (no-op). Replace with real modules/resources.
resource "null_resource" "placeholder" {
  provisioner "local-exec" {
    command = "echo infra/gcp/envs/dev placeholder"
  }
}

output "placeholder" {
  value = "infra/gcp/envs/dev configured"
}
