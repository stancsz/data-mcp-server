# DataMCP Infra & GitOps Roadmap

Purpose
-------
This document captures a practical, incremental plan to add infrastructure deployment and GitOps capabilities to this MCP server so it can manage, deploy, and support data applications and their infra lifecycle (Terraform, Helm, ArgoCD, GCP integration, CI/CD, and GitOps workflows).

High-level goals
----------------
- Provide MCP tools that can orchestrate infrastructure provisioning (Terraform), package and deploy apps (Helm), and manage GitOps (ArgoCD).
- Add GCP integration helpers (project creation, service accounts, IAM, GKE clusters, Cloud Storage).
- Expose safe, auditable operations through the MCP API (tool endpoints) so agents or humans can request infra actions.
- Ship opinionated scaffolds and example manifests to bootstrap a full-stack data app deployment.

Roadmap checklist
-----------------
- [x] Create infra plan document and initial checklist
- [ ] Scaffold directories for terraform, helm, argo, gcp, and ci
- [ ] Implement MCP tools for Terraform operations (plan, apply, destroy)
- [ ] Implement MCP tools for Helm operations (install/upgrade, rollback, uninstall)
- [ ] Implement MCP tools for ArgoCD integration (create App, sync, get status)
- [ ] Implement GCP helper tools (create project, create service account, grant IAM roles)
- [ ] Add SSO/credentials handling (secret storage + short-lived tokens)
- [ ] Add safe execution runner for shell/CLI operations (dry-run, sandboxed, idempotency)
- [ ] Add Terraform module registry or local modules for common infra (network, GKE, storage, IAM)
- [ ] Add example app (simple data app) with Helm chart and Terraform infra module
- [ ] Add GitOps repository layout examples and ArgoCD App manifests
- [ ] Integrate CI (GitHub Actions) to run linting, terraform fmt/check, helm lint, tests
- [ ] Add automated tests and CI integration for the MCP tools (unit + integration)
- [ ] Write docs for operators (how to run, security considerations, audit logs)
- [ ] Commit and push initial implementation and scaffolds
- [ ] Iterate on feedback and harden security (max UAT)

Initial scaffolding & file layout (proposed)
-------------------------------------------
- infra/terraform/           <-- terraform root & modules
  - modules/gke/
  - modules/network/
  - modules/gcs/
  - envs/dev/main.tf
  - envs/prod/main.tf
- infra/helm/
  - charts/example-data-app/
    - Chart.yaml
    - templates/
- infra/argocd/
  - apps/example-app.yaml
  - project.yaml
- infra/gcp/
  - scripts/create_project.sh
  - iam/roles.tf (terraform)
- infra/ci/
  - .github/workflows/infra-ci.yml
  - .github/workflows/app-deploy.yml
- docs/INFRA_PLAN.md        <-- this file
- docs/infra-readme.md      <-- operator docs & usage
- mcp_server.py             <-- add/mount new MCP tools (apply_terraform, helm_deploy, argo_sync, gcp_create_project)
- tools/runner.py           <-- safe command runner (exec wrappers, dry-run, logging, audit)
- secrets/ (gitignored)     <-- where credentials for automation are kept locally (not in repo)

MCP tool interface examples (API exposed via mcp.tool)
-----------------------------------------------------
- apply_terraform(env: str, workspace: Optional[str] = None, vars: Optional[dict] = None, auto_approve: bool = False) -> dict
  - runs terraform init/plan/apply in infra/terraform/envs/{env}
  - returns plan summary and apply output (IDs, resources)
- destroy_terraform(env: str, workspace: Optional[str] = None, auto_approve: bool = False) -> dict
- helm_deploy(chart: str, release_name: str, namespace: str, values: dict, repo: Optional[str] = None) -> dict
- helm_rollback(release_name: str, revision: int) -> dict
- argo_create_app(manifest_repo: str, path: str, dest_namespace: str, project: str) -> dict
- argo_sync(app_name: str) -> dict
- gcp_create_project(project_id: str, billing_account: str, org_id: Optional[str]) -> dict
- gcp_create_sa(project_id: str, name: str, roles: list[str]) -> dict

Security and operational considerations
---------------------------------------
- Never store long-lived credentials in the repo. Use secret stores (GCP Secret Manager, Vault) or require the operator to provide credentials via environment variables for local runs.
- All infra-executing MCP tools should support a dry-run mode and require explicit confirmation for destructive operations.
- Integrate operation logging/auditing so every MCP-driven infra action is recorded (who requested, what was run, timestamps, outputs).
- Rate-limit and add RBAC to MCP endpoints that can run infra to avoid accidental mass changes.

Next concrete step I will take (if you want me to proceed)
----------------------------------------------------------
1) Create the infra scaffolding files and a small safe command runner utility (tools/runner.py) plus add skeleton MCP tool wrappers in `mcp_server.py` for Terraform / Helm / Argo / GCP. This will be a non-destructive scaffold and local-only; no credentials changes will be made.  
2) Commit scaffolds to a new branch (e.g. `feat/infra-gitops`) and push the branch. (I will commit and push once we have procedural success as requested.)

If you want me to proceed, confirm:
- Create the scaffolding and MCP tool skeletons now and commit to a branch (I will push).
- OR: I should only create the scaffolding/docs and wait for your approval before modifying `mcp_server.py`.
