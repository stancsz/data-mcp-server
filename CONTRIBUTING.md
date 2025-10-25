# Contributing to data-mcp-server

Thanks for contributing. This guide describes how to open issues, submit PRs, and follow the project's conventions.

Before you start
- Read the main README for project goals and structure.
- Check existing issues to avoid duplicates.

How to submit a change
1. Fork the repository and create a feature branch:
   - git checkout -b feat/<short-description>
2. Keep changes small and focused. One feature or fix per PR.
3. Write tests for new behavior and ensure existing tests pass.
4. Run linters and formatters (if any) before committing.

Commit message conventions
- Use Conventional Commits: feat:, fix:, docs:, chore:, refactor:, test:, perf:
- Example: "feat: add BigQuery connector"

Pull request process
- Open a PR against `main`
- Provide a clear description and link to related issues
- CI should pass before merging
- At least one approval from a reviewer required

Code style and tests
- Use clear, descriptive function and variable names
- Add unit tests under `tests/` for new modules
- Avoid committing secrets or credentials

Issue templates and labels
- Use issue labels to categorize work: infra, core, connectors, pipelines, ci, docs

Contact & Governance
- Assign maintainers as project leads in the repo settings.
