# Cloud Infra Plans for DataMCP — AWS & GCP

This document provides concrete, actionable plans for AWS and GCP integration to support provisioning, deployment, and GitOps for data applications. It maps to the infra roadmap in docs/INFRA_PLAN.md and includes recommended Terraform modules, Helm/ArgoCD workflows, IAM/credentials handling, safety controls, audit, and a minimal PoC sequence.

Summary
-------
- Purpose: enable the MCP to orchestrate infra provisioning (Terraform), package & deploy applications (Helm), and manage GitOps (ArgoCD) across AWS and GCP.
- Scope: project-level automation (create projects/accounts), cluster provisioning (EKS/GKE), object storage (S3/GCS), RBAC/IAM, GitOps deployment pipelines, and safe execution from MCP tools.
- Deliverables:
  - Terraform modules (network, cluster, storage, IAM)
  - Helm charts for example data app
  - ArgoCD app manifests for GitOps
  - MCP tool wrappers (terraform, helm, argocd, gcloud/awscli helpers)
  - Documentation and safe-runner integration

Common Principles (applies to both clouds)
-----------------------------------------
- All destructive operations must support dry-run and explicit confirmation.
- Never store long-lived secrets in repo; use secret manager (AWS Secrets Manager / GCP Secret Manager) or operator-supplied credentials/environment.
- Audit every action: who requested, timestamp, params, outputs; store logs in a central place (Cloud logging/CloudWatch + persisted operation records in DynamoDB).
- Use Terraform remote state (S3 + DynamoDB locking for AWS; GCS + backend for GCP or Terraform Cloud) to avoid state corruption.
- Use short-lived service accounts / temporary creds where possible (STS for AWS; Workload Identity or impersonation for GCP).
- Keep minimal privileged service accounts for automation; require MFA/approval for elevated ops.

AWS Plan
--------
Target components:
- Projects: AWS accounts (or organizational OU) — note: creating AWS accounts requires Organization permissions; consider using a central infra account with Terraform + AWS Organizations.
- Networking: VPC, subnets, route tables, NAT, security groups (module: network).
- Compute/Kubernetes: EKS cluster module (best practice: separate node groups, managed nodegroups or node pools, OIDC provider for IRSA).
- Storage: S3 buckets, lifecycle/policy, encryption. Use bucket per environment and for Terraform remote state + DynamoDB for state locking.
- Database: RDS (if needed) via module.
- IAM: service accounts, roles, policies; restrict via least privilege.
- Observability: CloudWatch logs/metrics, and optional Prometheus/Grafana via Helm.
- GitOps: ArgoCD running in a cluster (EKS) or managed control plane; ArgoCD apps reference Helm charts in a git repo.

Terraform strategy:
- Directory layout:
  - infra/aws/modules/network/
  - infra/aws/modules/eks/
  - infra/aws/modules/s3/
  - infra/aws/envs/dev/main.tf
  - infra/aws/envs/prod/main.tf
- Backend:
  - s3 bucket for state (encrypted) + dynamodb for locking
- Workflows:
  - CI runs terraform fmt/tfsec/validate/plan then opens PR with plan output
  - apply gated to manual approval or CI with credentials in GitHub Actions with limited SA
- Example resources:
  - Create S3 bucket for app artifacts and Terraform state
  - Create EKS cluster with OIDC and IRSA for pods to assume IAM roles
  - Create service account & role for ArgoCD (or use ArgoCD with GitOps token)

ArgoCD + Helm on AWS:
- ArgoCD installed into a bootstrap cluster or managed EKS cluster.
- Helm charts stored in repo or packaged into ChartMuseum or OCI registry.
- ArgoCD Application manifests point to git repo path and target cluster/namespace.
- Access: ArgoCD server should be protected (SSO or restricted ingress).

Credentials & Security:
- Use AWS SSO or short-lived credentials via STS for operators.
- For automation (CI), create limited IAM role assumable by CI runner only for infra operations.
- Store secrets in AWS Secrets Manager and reference them in Kubernetes via ExternalSecrets or Secrets Store CSI.

Minimal AWS PoC sequence (manual dry-run first):
1. Create S3 bucket for Terraform state and DynamoDB table for state lock (manual or script).
2. Run terraform init in infra/aws/envs/dev with S3 backend configured (dry_run true in MCP tool).
3. terraform plan -> review
4. terraform apply (auto_approve only after manual confirmation or authorized role)
5. Create EKS cluster via module
6. Install ArgoCD with Helm (helm_deploy dry-run then real)
7. Push example Helm chart and create ArgoCD App referencing it
8. Sync ArgoCD App (argo_sync) and verify

GCP Plan
--------
Target components:
- Projects: GCP Projects per environment; Billing account linkage (requires Org permissions).
- Networking: VPC, subnets, firewall rules.
- Compute/Kubernetes: GKE Autopilot or Standard GKE cluster with node pools.
- Storage: GCS buckets for artifacts and Terraform remote state (or Terraform Cloud), and optionally Filestore.
- IAM: service accounts, roles, Workload Identity for Kubernetes.
- Observability: Stackdriver (Cloud Logging/Monitoring).
- GitOps: ArgoCD in GKE (or use Config Sync + Anthos for enterprise), Helm charts in repo or OCI registry.

Terraform strategy:
- Directory layout:
  - infra/gcp/modules/network/
  - infra/gcp/modules/gke/
  - infra/gcp/modules/gcs/
  - infra/gcp/envs/dev/main.tf
  - infra/gcp/envs/prod/main.tf
- Backend:
  - GCS bucket for state (with locking via special mechanisms; use Terraform Cloud if locking needed)
- Workflows:
  - CI runs terraform fmt/check/validate/plan and stores plan artifact
  - apply gated to a runner with service account key stored in secret manager or using workload identity in CI
- Example resources:
  - Create GKE cluster with Workload Identity enabled
  - Create GCS buckets for app artifacts & TF state
  - Create service accounts for ArgoCD & CI with minimal roles

ArgoCD + Helm on GCP:
- Install ArgoCD into GKE cluster using Helm.
- Use Workload Identity for ArgoCD to access GCP APIs if needed.
- Secure ArgoCD with OIDC (Google Workspace SSO) or GitHub OIDC.

Credentials & Security:
- Prefer Workload Identity and short-lived keys.
- Do not commit service account JSON keys to repo; if needed, store in Secret Manager (encrypted).
- For CI, use GitHub Actions workload identity federation to GCP (avoid storing JSON keys).

Minimal GCP PoC sequence:
1. Create GCS bucket for Terraform state (manual or script).
2. Run terraform init in infra/gcp/envs/dev (dry_run true initially).
3. terraform plan -> review
4. terraform apply with approved credentials
5. Create GKE cluster
6. Install ArgoCD via Helm
7. Create ArgoCD Application pointing to Helm chart repo
8. Sync via argo_sync MCP tool

MCP Tool Mappings (examples)
----------------------------
- apply_terraform(cloud: "aws" | "gcp", env: str, workspace: Optional[str], vars: dict, dry_run: bool=False, auto_approve: bool=False) -> dict
  - Locates infra/{cloud}/envs/{env} and runs terraform init/plan/apply via tools/runner.run_cmd
  - Uses configured backend (s3/gcs) and merges vars
  - Returns structured result: { plan_stdout, apply_stdout, returncode, succeeded: bool, summary: {...} }

- destroy_terraform(cloud, env, dry_run, auto_approve) -> dict

- helm_deploy(kube_context: Optional[str], chart_path: str, release: str, namespace: str, values: dict, dry_run: bool=False) -> dict
  - Runs helm upgrade --install (or helm uninstall)
  - Uses kubectl context or in-cluster service account

- argo_create_app(manifest_repo: str, path: str, app_name: str, dest_cluster: str, dest_namespace: str, project: str) -> dict
  - Applies ArgoCD Application manifest to argocd namespace (kubectl apply) or uses argocd CLI via runner

- argo_sync(app_name: str) -> dict
  - Uses argocd CLI: argocd app sync <app_name> or via ArgoCD REST API

- gcp_create_project(project_id: str, billing_account: str, org_id: Optional[str]) -> dict
  - Uses gcloud CLI with proper org permissions (shell executed via runner with dry_run support)
  - Returns created project metadata or errors

- aws_create_account(email: str, account_name: str, ou_id: Optional[str]) -> dict
  - Uses AWS Organizations APIs (prefer Terraform module) — must be performed from an org management account

Operational & Safety Patterns
-----------------------------
- All MCP tools that run CLI should:
  - Support dry_run: True by default for sensitive ops
  - Require explicit auto_approve flag for destructive ops
  - Validate inputs (project ids, region, syntactic checks)
  - Limit concurrency (lock per environment) to avoid parallel state mutation
  - Record an operation entry in a persistent store (DynamoDB table) for audit

- CI / GitHub Actions:
  - Use separate workflows for plan (on PR) and apply (manual approval on main).
  - Use OIDC federation for short-lived CI credentials (avoid secrets).
  - Run linters (terraform fmt, tflint, tfsec) and helm lint prior to apply.

Example folder scaffolding (to create)
--------------------------------------
infra/
  aws/
    modules/
      network/
      eks/
      s3/
    envs/
      dev/
        main.tf
        variables.tf
      prod/
  gcp/
    modules/
      network/
      gke/
      gcs/
    envs/
      dev/
      prod/
  helm/
    charts/
      example-data-app/
  argocd/
    apps/
      example-app.yaml

Audit & Logging
---------------
- Persist an operations log: DynamoDB table "mcp_ops_log" with:
  - id, user, tool, params, start_ts, end_ts, status, stdout, stderr, resource_refs
- Forward logs to Cloud logging (CloudWatch / Stackdriver) for centralized monitoring.
- Optionally push operation artifacts (terraform plan output) to object storage for retention.

Next steps (recommended immediate tasks)
---------------------------------------
- [ ] Create infra/ folder scaffolding for AWS/GCP (modules + envs) and add minimal example main.tf files.
- [ ] Add GitHub Actions workflow templates: infra-plan (PR) and infra-apply (protected, manual).
- [ ] Add MCP tool skeletons to mcp_server.py mapping to runner.run_cmd (non-destructive default).
- [ ] Create simple Helm chart for example-data-app and ArgoCD Application manifest.
- [ ] Implement audit persistence for operation records.
- [ ] Commit scaffolds to branch feat/infra-gitops and push for review.

Appendix: Quick checks before running any infra tool from MCP
--------------------------------------------------------------
- Ensure terraform binary is available in PATH on runner host.
- Ensure helm, kubectl, gcloud, aws CLI versions are compatible and available.
- Ensure operator/CI has appropriate permissions and that credentials are not stored in repo.
- Run small test in a sandbox environment (dev) with dry_run True.
