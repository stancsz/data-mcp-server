import os
import difflib
import yaml

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def file_diff(before, after, filename):
    diff = difflib.unified_diff(
        before.splitlines(keepends=True),
        after.splitlines(keepends=True),
        fromfile=f"{filename} (before)",
        tofile=f"{filename} (after)",
    )
    return "".join(diff)

def write_pr_yaml(path, title, body, branch):
    pr_data = {
        "title": title,
        "body": body,
        "branch": branch
    }
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(pr_data, f, sort_keys=False, allow_unicode=True)

import random
from datetime import datetime, timedelta

def write_git_sh(path, branch, commit_steps):
    """
    Write a git.sh script that:
    - Creates a branch
    - For each commit step (dict with 'file', 'msg'), adds/commits with randomized timestamp
    - Pushes the branch at the end

    commit_steps: list of dicts, each with:
        - 'file': file path to add
        - 'msg': commit message
    """
    script = "#!/bin/sh\nset -e\n"
    script += f"git checkout -b {branch}\n"

    # Start time: now
    base_time = datetime.now()
    for i, step in enumerate(commit_steps):
        # Random offset: 10-20 min
        offset = random.randint(10, 20)
        base_time += timedelta(minutes=offset)
        ts = base_time.strftime("%Y-%m-%dT%H:%M:%S")
        script += f'export GIT_COMMITTER_DATE="{ts}"\n'
        script += f'export GIT_AUTHOR_DATE="{ts}"\n'
        script += f'git add "{step["file"]}"\n'
        script += f'git commit -m "{step["msg"]}"\n'

    script += f"git push origin {branch}\n"
    script += 'echo "Now run: gh pr create -F pr.yaml"\n'

    with open(path, "w", encoding="utf-8") as f:
        f.write(script)
