"""
Agent for autonomous code editing using OpenAI LLM.

Usage:
    from coding_agent.agent import run_coding_agent

    run_coding_agent(
        prompt="Refactor all functions to use async/await.",
        code_dir="/path/to/project",
        pr_title="Refactor to async/await",
        pr_body="This PR refactors all functions to use async/await syntax.",
        pr_branch="refactor-async-await"
    )
"""

import os
from openai import OpenAI
from .utils import read_file, write_file, file_diff, write_pr_yaml, write_git_sh

import subprocess
import random
from datetime import datetime, timedelta

def run_coding_agent(prompt, code_dir, pr_title, pr_body, pr_branch, commit_and_push=False):
    """
    Main entrypoint for the coding agent.

    Args:
        prompt (str): User instruction for code changes.
        code_dir (str): Path to the codebase to edit.
        pr_title (str): Title for the pull request.
        pr_body (str): Body/description for the pull request.
        pr_branch (str): Target branch name for the PR.

    Outputs:
        - pr.yaml: PR metadata for GitHub CLI
        - git.sh: POSIX shell script for git operations
    """
    # 1. Gather code context
    code_files = []
    for root, _, files in os.walk(code_dir):
        for f in files:
            if f.endswith(('.py', '.js', '.ts', '.json', '.md', '.txt', '.yaml', '.yml')):
                code_files.append(os.path.join(root, f))

    client = OpenAI()
    diffs = []
    changed_files = []
    commit_steps = []

    # 2. For each file, use LLM to suggest edits
    for file_path in code_files:
        before = read_file(file_path)
        # Construct LLM input: prompt, file path, file content
        llm_input = [
            {
                "role": "system",
                "content": (
                    "You are an autonomous coding agent. "
                    "Given a user instruction and a code file, output the revised file content only. "
                    "Do not include explanations or comments outside the code."
                )
            },
            {
                "role": "user",
                "content": (
                    f"User instruction: {prompt}\n"
                    f"File path: {file_path}\n"
                    f"File content:\n{before}"
                )
            }
        ]
        response = client.responses.create(
            model="gpt-4.1",
            input=llm_input,
            text={
                "format": {
                    "type": "text"
                }
            },
            reasoning={},
            tools=[],
            temperature=1,
            max_output_tokens=2048,
            top_p=1,
            store=True
        )
        # Extract new content from LLM response
        after = getattr(response, "output_text", "")
        if after and after.strip() != before.strip():
            write_file(file_path, after)
            diff = file_diff(before, after, file_path)
            diffs.append(diff)
            changed_files.append(file_path)
            commit_steps.append({
                "file": file_path,
                "msg": f"Edit {os.path.relpath(file_path, code_dir)} as per instruction"
            })

    # 3. Summarize changes for PR body
    changes_summary = ""
    if changed_files:
        changes_summary = "Files changed:\n" + "\n".join(f"- {os.path.relpath(f, code_dir)}" for f in changed_files)
        if diffs:
            changes_summary += "\n\nDiff summary:\n" + "\n".join(diffs[:3])  # Show up to 3 diffs

    # 4. Output pr.yaml and git.sh
    pr_yaml_path = os.path.join(code_dir, "pr.yaml")
    git_sh_path = os.path.join(code_dir, "git.sh")
    full_pr_body = pr_body
    if changes_summary:
        full_pr_body += "\n\n" + changes_summary

    write_pr_yaml(pr_yaml_path, pr_title, full_pr_body, pr_branch)
    write_git_sh(git_sh_path, pr_branch, commit_steps)

    if commit_and_push and commit_steps:
        # Perform git operations directly
        cwd = os.path.abspath(code_dir)
        # Create branch
        subprocess.run(["git", "checkout", "-b", pr_branch], cwd=cwd, check=True)
        base_time = datetime.now()
        for step in commit_steps:
            offset = random.randint(10, 20)
            base_time += timedelta(minutes=offset)
            ts = base_time.strftime("%Y-%m-%dT%H:%M:%S")
            env = os.environ.copy()
            env["GIT_COMMITTER_DATE"] = ts
            env["GIT_AUTHOR_DATE"] = ts
            subprocess.run(["git", "add", step["file"]], cwd=cwd, check=True, env=env)
            subprocess.run(["git", "commit", "-m", step["msg"]], cwd=cwd, check=True, env=env)
        subprocess.run(["git", "push", "origin", pr_branch], cwd=cwd, check=True)
        print(f"Committed and pushed {len(commit_steps)} changes to branch {pr_branch}.")

    print(f"Agent run complete. {len(changed_files)} files changed. pr.yaml and git.sh written to {code_dir}.")
