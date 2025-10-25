# Project TODO / Team Roadmap

This document defines the recommended workstreams, deliverables, priorities, and an actionable checklist for teams to implement the data-mcp-server vision.

Legend
- [ ] incomplete
- [x] complete

Overall priorities
1. Stabilize MCP server and RBAC
2. Provide end-to-end pipeline examples (batch + streaming)
3. Expand connectors and integration tests
4. Harden infra and CI/CD for cloud deployments

High-level workstreams (teams)
- Infrastructure Team
  - Scope: Terraform modules, environment provisioning, EKS/GKE, networking, IAM
  - Deliverables: reusable Terraform modules, documented dev/prod envs, remote state example

- Core MCP & Server Team
  - Scope: MCP server runtime, API surface, auth/RBAC, CLI & client SDKs
  - Deliverables: auth integration (OIDC/IAM), pipeline registry API, health checks, metrics

- Connectors Team
  - Scope: cloud connectors and common source connectors (RDBMS, S3/GCS, Pub/Sub/Kinesis, Kafka, APIs)
  - Deliverables: connection patterns, retry/backoff, pagination, schema inference

- Pipelines & Templates Team
  - Scope: pipeline definitions, runnable templates, notebook examples, ML-data workflows
  - Deliverables: ingestion templates, ETL templates (Spark/Pandas/SQL), streaming templates, ML data-prep + training examples

- DevOps / CI Team
  - Scope: CI/CD, image builds, infra pipelines (terraform), test orchestration
  - Deliverables: GitHub Actions for build/test/deploy, integration test runners, gated applies

- Docs & QA
  - Scope: docs, runbooks, onboarding, test coverage
  - Deliverables: reproducible guides, test matrices, example datasets

Project-level checklist
- [x] Rewrite repository README with goals and next steps
- [ ] Create docs/TODO.md (this file) and distribute to teams
- [ ] Define and publish maintainers and team leads
- [ ] Add LICENSE file and contributor guide

Infra & deployment
- [ ] Standardize Terraform remote state backend and example prod env
- [ ] Harden IAM roles and least-privilege examples
- [ ] Provide Terraform module docs and examples for:
  - [ ] networking (VPC/subnets)
  - [ ] EKS/GKE cluster and node pools
  - [ ] storage (S3/GCS) and lifecycle policies
  - [ ] RBAC / service accounts
- [ ] Provide Helm charts and manifests for deploying:
  - [ ] MCP server (with configurable auth)
  - [ ] pipeline-runner job/controller
  - [ ] example-data-app

MCP server & platform
- [ ] Implement auth & RBAC with at least one provider (OIDC / AWS IAM / GCP IAM)
- [ ] Add healthz, readiness, and metrics (Prometheus)
- [ ] Implement pipeline registry (CRUD) and versioning
- [ ] Add CLI to scaffold and register pipelines
- [ ] Provide sample policies/roles for pipeline execution

Connectors & clients
- [x] Inventory existing connectors under aws/ and gcp/
- [ ] Add connector test harness and local mocking
- [ ] Implement schema inference and sample mapping tools
- [ ] Add common source connectors:
  - [ ] PostgreSQL (JDBC)
  - [ ] MySQL (JDBC)
  - [ ] Kafka
  - [ ] Generic REST API connector
  - [ ] Salesforce / SaaS connectors (stretch)

Pipeline templates & examples
- [ ] Batch ingestion: S3/GCS -> staging -> warehouse (Athena/BigQuery)
- [ ] Scheduled SQL analytics: Athena/BigQuery query runner templates
- [ ] Streaming: Kinesis/Firehose or Pub/Sub -> transforms -> sink
- [ ] ETL: Spark (EMR/Dataproc) + Pandas templates for small jobs
- [ ] ML data pipelines: feature extraction, training job orchestration, model storage
- [ ] Notebook examples for ad-hoc exploration (Jupyter/Colab)

Testing & CI
- [ ] Unit tests for all connector modules (mocked cloud clients)
- [ ] Integration tests (optional, require cloud creds)
- [ ] End-to-end smoke tests for each pipeline template
- [ ] Add test matrix to CI: python versions, cloud provider flags

Security & secrets
- [ ] Document secret management patterns for AWS and GCP
- [ ] Integrate Secrets Manager / Secret Manager CI patterns
- [ ] Add automated scanning for secrets in CI

Operational runbooks
- [ ] Create runbooks for common incidents:
  - [ ] Connector failures / throttling
  - [ ] Infra drift / Terraform rollback
  - [ ] Pipeline job retries and poison message handling
- [ ] Add monitoring dashboards examples

Developer experience
- [ ] Add `scripts/` or `tools/` helpers to scaffold new connectors / pipelines
- [ ] Add local dev mode for running MCP server + mocked connectors
- [ ] Provide scaffold CLI to create pipeline definitions

Milestones (first 90 days)
- Week 1–2: Stabilize README, TODO doc, assign teams, define maintainers
- Week 3–6: Core MCP auth, pipeline registry, Terraform dev env documented
- Week 7–10: End-to-end batch example + CI for basic integration tests
- Week 11–12: Streaming example, connector improvements, and runbooks

How to use this roadmap
- Team leads should claim checklist items by opening GitHub issues and linking to this doc
- Break large checklist items into smaller tickets with clear acceptance criteria
- Use labels: infra, core, connectors, pipelines, ci, docs

Appendix: Suggested issue templates (use in repo .github/ISSUE_TEMPLATE)
- New connector request
- Pipeline template submission
- Infra change (Terraform)
- Bug report / incident
