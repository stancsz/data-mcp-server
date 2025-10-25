# data-mcp-server

A practical, production-minded MCP (Model Context Protocol) server for orchestrating data pipelines across AWS and GCP. Designed to provide reusable, configurable ingestion, transformation, analytics, and data-science pipelines (batch + streaming) for common sources and sinks — with infrastructure-as-code, examples, and connector clients out-of-the-box.

This repository is an opinionated starter-kit for teams building data engineering and ML-data pipelines that need:
- Multi-cloud support (AWS & GCP)
- Connector clients for common services (S3, Kinesis, Firehose, Athena, BigQuery, Pub/Sub, GCS, etc.)
- Deployable infra modules (Terraform + Helm charts)
- A practical MCP server to expose pipelines and tooling as programmatic services
- Templates for ingestion, transformation, analytics, and model training pipelines (Python, SQL, notebooks)

Goals
- Make it straightforward to provision cloud infra for data pipelines (dev -> prod)
- Provide a modular MCP server that exposes pipeline orchestration and connector utilities
- Ship practical examples and templates for batch, stream, ETL/ELT, and ML pipelines
- Be team-friendly: clear repo structure, recommended team responsibilities, and contribution guidance

Key features
- Connector clients for AWS and GCP (see aws/ and gcp/ folders)
- Infrastructure modules and envs for AWS EKS + networking and GCP envs (infra/)
- Example Helm chart for deploying a data application (infra/helm/)
- Test suite skeleton and utilities (tests/)
- A minimal MCP server entrypoint (mcp_server.py) and client helper (mcp_client.py)

Repository layout
- mcp_server.py, mcp_client.py — Minimal MCP server and client interface
- aws/ — AWS connector modules (S3, Kinesis, Athena, Glue, Redshift, EMR, Lambda, Step Functions, etc.)
- gcp/ — GCP connector modules (BigQuery, Pub/Sub, GCS, Secret Manager, IAM)
- infra/ — Terraform modules, environment configs, Helm charts for deploying example workloads
- docs/ — Project docs, infra plans, agent-related design notes
- tests/ — Unit tests and integration test skeletons
- tools/ — Helper scripts for local dev and automation

Quick start (local development)
Prerequisites:
- Python 3.9+ and pip
- Terraform (for infra)
- kubectl, helm (to deploy to k8s)
- Cloud CLIs if you plan to deploy (awscli, gcloud)

1. Create a virtualenv and install deps
```bash
python -m venv .venv
.venv/Scripts/activate    # Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -r requirements.txt || pip install pytest
```

2. Run the MCP server locally
```bash
python mcp_server.py
```
This runs the local MCP server used to register and serve pipeline-related actions. See `mcp_client.py` for example usage.

3. Run tests
```bash
pytest -q
```

How pipelines are modeled
- Config-driven pipelines: YAML/JSON definitions that describe sources, transforms, destinations, schedule/triggers, and runtime image/runtime (Python, Spark, SQL, Notebook).
- Implementations: small Python pipeline templates (aws/glue + databricks/EMR hooks), SQL-first workflows that push queries to Athena/BigQuery, and streaming templates using Kinesis/Firehose and Pub/Sub.
- Example pipeline types:
  - Ingestion: S3/GCS ingestion, API pullers, JDBC ingestion
  - ETL/ELT: Spark/Pandas jobs, Glue jobs, BigQuery SQL jobs
  - Streaming: Kinesis/Firehose -> Lambda/Glue -> S3/BigQuery
  - Analytics: scheduled SQL jobs (Athena/BigQuery), ad-hoc notebooks
  - ML: data preparation pipelines, training job orchestration, model artifacts storage

Deployment & infra overview
- Terraform modules provided in infra/aws/modules and infra/gcp/envs for environment scaffolding
- Charts in infra/helm/charts/example-data-app show how to package a data app for k8s
- Typical deployment flow:
  1. Provision cloud infra (Terraform): networking, EKS/GKE, IAM roles, storage
  2. Build and push container images for pipeline runners
  3. Deploy MCP server + operator/cron jobs to the cluster (Helm)
  4. Register pipeline definitions in the MCP server or via CI/CD

Security and secrets
- Do not commit credentials. Use parameter stores / secret managers:
  - AWS: Secrets Manager / SSM (aws/secretsmanager_client.py, aws/ssm_client.py)
  - GCP: Secret Manager (gcp/secret_manager_client.py)
- Service accounts and least-privilege IAM roles are required in infra plans (see infra/README.md and docs/CLOUD_INFRA_PLANS.md)

Extending connectors & pipelines
- Add new connector clients under aws/ or gcp/ following the existing client patterns
- Add pipeline templates under a new templates/ directory or infra/helm for k8s jobs
- Provide automated tests in tests/ for each connector and pipeline template

CI/CD
- GitHub Actions CI pipeline exists in .github/workflows/ci.yml. Extend with integration tests that require cloud credentials stored as GitHub secrets.
- Recommended: Separate pipelines for infra (Terraform plan/apply), build/push images, and deployment (Helm)

Teams & recommended responsibilities
- Infrastructure Team: Terraform modules, network/security, provisioning EKS/GKE, IAM roles
- Core MCP & Server Team: MCP server improvements, CLI, endpoint contracts, auth
- Connectors Team: Implement and maintain AWS/GCP connectors, drivers, integration tests
- Pipelines & Templates Team: Build examples for ingestion, ETL/ELT, streaming and ML; provide runnable templates
- DevOps/CI Team: CI/CD pipelines, image building, release process, policies
- Docs & QA: Maintain docs/, run integration tests, verify reproducible guides

Suggested roadmap (high level)
- [ ] Harden auth & RBAC for MCP server
- [ ] Add end-to-end examples for batch + streaming pipelines
- [ ] Provide a CLI to scaffold new pipeline definitions
- [ ] Add more connector coverage (Databases, Salesforce, Kafka, etc.)
- [ ] Publish Terraform remote state backend & example prod env

Contributing
- Follow conventional commits and open PRs to the main branch
- Add tests for new connectors and pipeline templates
- Update docs/ with any infra or API changes

Where to look next in this repo
- Start with docs/README_FASTMCP.md and docs/README.md for agent and MCP design notes
- Inspect aws/ and gcp/ folders to see available connector clients
- Review infra/README.md and infra/aws/envs/dev/main.tf for an opinionated dev infra example
- mcp_server.py for the MCP server entrypoint; mcp_client.py for client usage examples

Contact & governance
- Project lead / maintainer: (assign maintainer contact here)
- Use GitHub issues for task tracking and team assignment

License
- Add your preferred license in LICENSE file.

This README is intentionally concise but practical. Expand per-team with specific process docs, runbooks, and example pipeline definitions as teams are assigned.
