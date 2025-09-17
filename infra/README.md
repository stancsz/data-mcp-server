# Infra Scaffolding for DataMCP

This directory will hold Terraform, Helm, and ArgoCD manifests used by the MCP server to provision and deploy infra/applications.

Planned layout (create files under these paths as you implement):
- infra/
  - aws/
    - modules/
      - network/
      - eks/
      - s3/
    - envs/
      - dev/
        - main.tf        # Terraform root for dev environment (backend config + module usage)
      - prod/
  - gcp/
    - modules/
      - network/
      - gke/
      - gcs/
    - envs/
      - dev/
        - main.tf
      - prod/
  - helm/
    - charts/
      - example-data-app/
        - Chart.yaml
        - values.yaml
        - templates/
  - argocd/
    - apps/
      - example-app.yaml

Example Terraform backend snippets (place in infra/aws/envs/dev/backend.tf or main.tf):

# AWS S3 backend (example)
# terraform {
#   backend "s3" {
#     bucket         = "my-terraform-state-bucket"
#     key            = "data-mcp/aws/dev/terraform.tfstate"
#     region         = "us-central1"
#     dynamodb_table = "mcp-terraform-locks"
#     encrypt        = true
#   }
# }

# GCP GCS backend (example)
# terraform {
#   backend "gcs" {
#     bucket  = "my-terraform-state-bucket-gcp"
#     prefix  = "data-mcp/gcp/dev"
#   }
# }

Safety & usage notes
- Keep `dry_run` enabled in MCP tools until you're confident in the flows.
- Do NOT commit service account keys, long-lived credentials, or secrets to the repo.
- Use remote state (S3+DynamoDB or GCS) with locking to prevent concurrent state mutation.
- Add CI pipelines: plan on PRs, apply on protected branches with approval.

Next steps to implement (recommended)
- [ ] Create minimal Terraform root files in infra/aws/envs/dev and infra/gcp/envs/dev
- [ ] Create simple Helm chart for example-data-app
- [ ] Add ArgoCD Application manifest in infra/argocd/apps/example-app.yaml
- [ ] Add GitHub Actions workflows for infra plan (PR) and infra apply (manual)
- [ ] Add MCP tool skeletons in `mcp_server.py` that call `tools/runner.run_cmd` (dry-run default)
- [ ] Commit changes to branch `feat/infra-gitops` and push
