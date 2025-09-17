# MCP Server Implementation Plan — S3 + Dynamo Integration (agent notes)

## Goal
Implement an MCP server (FastMCP scaffold) with working AWS S3 and DynamoDB integrations, including:
- Server handlers exposing S3 + Dynamo operations
- Proper configuration (env / local dev)
- Unit/integration tests (manual or automated)
- Dependency installation and CI hooks
- Commit history on branch `feature/mcp-s3-dynamo`

## Assumptions
- AWS credentials (ACCESS_KEY_ID, SECRET_ACCESS_KEY, AWS_REGION) will be provided via environment variables or an AWS profile.
- If the user wants local testing without AWS, we can use LocalStack (optional).
- Repository root contains `mcp_server.py` (FastMCP scaffold) to be extended.
- We'll use `boto3` (sync) for AWS integrations. Optionally add `aioboto3` if async needed.

## High-level steps (iteration plan)
1. Prepare repo
   - Create branch (done)
   - Add this plan file under docs/agent (done)
2. Add dependencies
   - Add `boto3` to `pyproject.toml` (and optionally `python-dotenv`, `localstack-client` for local testing)
   - Install packages locally (pip/hatch)
3. Create config helpers
   - `config.py` (read env vars, support .env via python-dotenv)
4. Create AWS wrapper modules
   - `aws/s3_client.py` — wrapper for S3 operations (upload, download, list, delete, presign)
   - `aws/dynamo_client.py` — wrapper for DynamoDB operations (put_item, get_item, query, delete)
5. Integrate into MCP server
   - Update `mcp_server.py`:
     - Initialize FastMCP server and register endpoints / handlers that call the AWS wrappers
     - Provide necessary authentication/authorization hooks (basic for now)
6. Tests & local verification
   - Add small integration script `scripts/manual_test.py` or tests under `tests/`
   - Optionally use LocalStack for offline testing
7. CI
   - Add GitHub Actions workflow for lint, unit tests, and optional integration test against LocalStack
8. Finalize
   - Run tests, fix issues, commit, push

## Files to create / modify
- Modify:
  - `pyproject.toml` -> add boto3, python-dotenv (optional)
  - `mcp_server.py` -> add endpoints, integrate wrappers
- New:
  - `docs/agent/MCP_PLAN.md` (this file)
  - `aws/s3_client.py`
  - `aws/dynamo_client.py`
  - `config.py`
  - `tests/test_s3_dynamo.py` (integration or unit tests)
  - `.github/workflows/ci.yml` (CI)

## Implementation details — S3
- Use boto3 client for S3:
  - Functions: upload_fileobj(bucket, key, fileobj), download_fileobj(bucket, key) -> BytesIO, list_objects(bucket, prefix), delete_object(bucket,key), generate_presigned_url(bucket,key,expires_in)
- Use config to set default bucket(s)

## Implementation details — DynamoDB
- Use boto3 resource or client:
  - Functions: put_item(table, item), get_item(table, key), query(table, key_expr), delete_item(table, key)
- Use typed helpers to convert between Python dicts and Dynamo item format (boto3 handles this via resource).

## Environment & installation
- Add to pyproject.toml dependencies:
  - "boto3"
  - optionally "python-dotenv" (for local .env)
  - optionally "localstack-client" or "localstack" if user wants local integration
- Install packages:
  - `python -m pip install -r requirements.txt` or with hatch: `hatch run pip install .` (we'll choose pip install boto3 for quick dev)

## Security & IAM
- Recommend creating an IAM user/role with least privilege for S3 & Dynamo operations the server needs.
- Do NOT commit credentials to the repo.

## Repository directory guide
This project is organized to separate runtime code, infra scaffolding, documentation, and tests. Use this guide when adding files or modifying structure.

Top-level layout (current)
- .github/                      -> CI workflows and GitHub configurations
- aws/                          -> AWS service wrappers (s3_client.py, dynamo_client.py)
- infra/                        -> Terraform / Helm / ArgoCD scaffolding and modules
  - aws/                        -> AWS-specific TF modules + envs
  - gcp/                        -> GCP-specific TF modules + envs
  - helm/                       -> Helm chart(s) for example apps
  - argocd/                     -> ArgoCD application manifests
- docs/                         -> Project documentation and plans
  - agent/                      -> Implementation plans and agent-facing guides (this folder)
- tools/                        -> Utility scripts used by MCP (runner, scripts)
- tests/                        -> Unit/integration tests
- config.py                     -> Configuration helpers (env, .env support)
- mcp_server.py                 -> FastMCP server entrypoint and tool registrations
- mcp_client.py                 -> Example client for interacting with the MCP server
- pyproject.toml                -> Python project metadata and dependencies

Directory guidance / responsibilities
- Keep production-safe credentials and long-lived keys out of the repo. Use `secrets/` (gitignored) or operator-provided env variables.
- Put infrastructure code inside `infra/` and keep env-specific roots under `infra/{cloud}/envs/{env}`.
- Use modules under `infra/{cloud}/modules/` for reusable components (network, k8s, storage).
- Use `docs/agent/` for human-readable step-by-step implementation instructions, PR checklists, and branch notes.
- `tools/runner.py` contains a safe command runner used by MCP tool wrappers — do not expose sensitive output directly without audit logging.

Contributing & workflow notes
- Create feature branches named `feat/<short-desc>` or `fix/<short-desc>`.
- Open PRs against `main` with a description of changes and any required operator steps (e.g., "create S3 state bucket before applying").
- Run CI locally where possible (pytest, flake8/black) and ensure terraform/helm lint steps pass in CI.
- For infra changes:
  - Add terraform module code under `infra/.../modules/`
  - Add env root under `infra/.../envs/<env>`
  - Add or update backend configuration to point at remote state (S3 or GCS) — document required buckets/tables in docs/infra-readme.md
- For Helm charts:
  - Place charts under `infra/helm/charts/` and include a Chart.yaml, values.yaml, and templates.
  - Use `helm lint` locally and in CI.

## Next immediate actions (first iteration)
- [ ] Update `pyproject.toml` to include `boto3` and `python-dotenv`.
- [ ] Create `config.py`.
- [ ] Create `aws/s3_client.py` and `aws/dynamo_client.py` with basic functionality.
- [ ] Modify `mcp_server.py` to register endpoints that call these wrappers (already partially done).
- [ ] Add ArgoCD and Helm manifests to infra/ and a simple example app chart (in progress).
- [ ] Add GitHub Actions workflows for infra plans and gated applies.

## Notes / Questions for user
- Confirm whether to use LocalStack for offline testing, or target real AWS directly.
- Confirm preferred async model: keep synchronous (boto3) or switch to async (`aioboto3`)?
- Confirm whether you want me to create a `docs/agent/REPO_STRUCTURE.md` separate from this file (I added the repository guide above; I can split if you prefer).
