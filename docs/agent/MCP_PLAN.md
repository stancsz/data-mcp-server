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

## Next immediate actions (first iteration)
- [ ] Update `pyproject.toml` to include `boto3` and `python-dotenv`.
- [ ] Create `config.py`.
- [ ] Create `aws/s3_client.py` and `aws/dynamo_client.py` with basic functionality.
- [ ] Modify `mcp_server.py` to register endpoints that call these wrappers.
- [ ] pip install boto3 (local dev).
- [ ] Run simple manual verification.

## Notes / Questions for user
- Confirm whether to use LocalStack for offline testing, or target real AWS directly.
- Confirm preferred async model: keep synchronous (boto3) or switch to async (`aioboto3`)?
