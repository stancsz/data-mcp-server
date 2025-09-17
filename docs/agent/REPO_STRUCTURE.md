# Repo Structure & Directory Guide (DataMCP)

This document explains the repository layout, conventions, and examples so contributors and operators can find code, infra, and docs quickly.

Purpose
-------
Provide a single reference that maps directories/files to responsibilities, example usage patterns, and where to place new artifacts (Terraform, Helm, ArgoCD, CI, docs, tests).

Top-level layout
----------------
- .github/                      -> CI workflows, PR and issue templates
- aws/                          -> AWS helper wrappers (s3_client.py, dynamo_client.py)
- infra/                        -> Infrastructure scaffolding (Terraform, Helm, ArgoCD)
  - aws/                        -> AWS-specific TF modules + env roots
    - modules/                   -> Reusable terraform modules (network, eks, s3, etc)
    - envs/                      -> Environment roots (dev/, prod/) that call modules
  - gcp/                        -> GCP-specific TF modules + env roots
  - helm/                       -> Helm charts (charts/<chart-name>/...)
  - argocd/                      -> ArgoCD application manifests (apps/*.yaml)
- docs/                         -> High-level docs and planning
  - agent/                      -> Implementation plans, repo guides, PR checklists
  - INFRA_PLAN.md               -> Infra roadmap
  - CLOUD_INFRA_PLANS.md        -> Cloud-specific plans for AWS/GCP
- tools/                        -> Helper scripts and utilities (runner.py, scripts/)
- tests/                        -> Unit and integration tests
- config.py                     -> Runtime configuration (env/.env loading helpers)
- mcp_server.py                 -> FastMCP server entrypoint and tool registrations
- mcp_client.py                 -> Example client showing how to call tools
- pyproject.toml                -> Python metadata and dependencies
- .gitignore                    -> Files and sensitive patterns to ignore

Conventions
-----------
- Branches:
  - feat/<short-desc> for new features
  - fix/<short-desc> for bug fixes
  - chore/<short-desc> for maintenance
  - Open PRs against main; include testing/operational notes in the PR description.
- Commits: use conventional commit-style messages: feat(...), fix(...), chore(...)
- Secrets: never commit service account keys, JSON credentials, or terraform tfvars files with secrets. Use `secrets/` (gitignored) locally or a secret manager in production.
- Remote state: use S3+DynamoDB for AWS backends, GCS for GCP, or Terraform Cloud. Document required state buckets/tables in docs/infra-readme.md.

Where to add Terraform code
---------------------------
- Create module code in: infra/<cloud>/modules/<module_name>/
  - Keep modules small and focused (network, cluster, storage, iam).
  - Provide variables.tf, outputs.tf, main.tf inside each module.
- Create environment roots in: infra/<cloud>/envs/<env>/
  - terraform { backend "s3" {...} } or backend "gcs" should be configured here or referenced via backend.tf.
  - These roots call modules and define environment variables / inputs.

Where to add Helm charts
------------------------
- Add charts under: infra/helm/charts/<chart-name>/
  - Required: Chart.yaml, values.yaml, templates/
  - Run `helm lint` locally and in CI before merging.

Where to add ArgoCD manifests
-----------------------------
- Add ArgoCD Application manifests under: infra/argocd/apps/
  - A manifest should point at a Git repo/path (often within this repository's infra/helm or a separate app repo) and reference target cluster/namespace.
  - Protect ArgoCD server access; use SSO/OIDC in production.

Tools & Runner
--------------
- tools/runner.py: safe command runner used by mcp_server tool wrappers (supports dry_run)
- Any script that executes infra tooling should use tools/runner.run_cmd to centralize logging and dry-run behavior.

Testing & CI
------------
- Tests go under tests/. Prefer small unit tests for wrappers and integration tests for end-to-end flows.
- CI workflows (in .github/workflows/) should include:
  - lint (black/flake8/isort)
  - test (pytest)
  - infra-plan (on PR): run terraform fmt, terraform init/plan (dry-run), helm lint
  - infra-apply (manual on main): runs apply with protected approval
- Use OIDC/workload identity for CI to authenticate to cloud providers rather than long-lived keys stored in the repo.

Audit & Logging
---------------
- All operations that mutate infra must be auditable. Recommended:
  - Persist operation records (DynamoDB table `mcp_ops_log` or equivalent) with: id, user, tool, params, start_ts, end_ts, status, stdout, stderr, resource_refs.
  - Forward stdout/stderr or structured logs to CloudWatch / Stackdriver for central observability (mask secrets).

Examples
--------
1) Adding a new Terraform module
   - Create: infra/aws/modules/my-module/{main.tf,variables.tf,outputs.tf}
   - Reference from env: infra/aws/envs/dev/main.tf
   - Test locally: terraform init && terraform plan (use a sandbox backend or local backend)
   - Add CI linting: terraform fmt, tflint

2) Adding a Helm chart
   - Create: infra/helm/charts/my-app/{Chart.yaml,values.yaml,templates/*}
   - Locally test: helm lint infra/helm/charts/my-app
   - Add ArgoCD App: infra/argocd/apps/my-app.yaml referencing the chart repo or path

3) Adding an MCP tool that runs Terraform
   - Implement a wrapper in mcp_server.py that calls tools/runner.run_cmd (dry_run default)
   - Validate inputs, write a short plan output to the ops log, and return a structured response to the caller.

Repository housekeeping checklist
-------------------------------
- [ ] Ensure .gitignore covers terraform state, credentials, and local env files (done)
- [ ] Add infra/argocd/ and infra/helm/ examples (in progress)
- [ ] Add module READMEs describing inputs/outputs for each Terraform module
- [ ] Ensure all tooling invocations are wrapped with tools/runner for auditability
- [ ] Create a CONTRIBUTING.md with PR templates and code style rules

Next recommended docs to add
---------------------------
- docs/infra-readme.md — operator-facing instructions to bootstrap remote state & run example dev deploy
- docs/agent/RELEASE_NOTES.md — changelog guidance for infra changes
- docs/SECURITY.md — security practices for credential handling and RBAC

Where to get help
-----------------
- For infra-specific questions, check docs/CLOUD_INFRA_PLANS.md first.
- For MCP tool behavior, inspect mcp_server.py and tools/runner.py.
- For CI questions, review .github/workflows/*.
