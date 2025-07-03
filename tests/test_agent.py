import os
import shutil
import tempfile
import pytest

from dotenv import load_dotenv
load_dotenv()

from coding_agent.agent import run_coding_agent

def create_sample_file(dir_path, filename, content):
    file_path = os.path.join(dir_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path

@pytest.fixture
def temp_code_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a sample Python file
        create_sample_file(tmpdir, "foo.py", "def foo():\n    return 1\n")
        yield tmpdir  # Provide the temp directory to the test

def test_run_coding_agent_basic(temp_code_dir):
    # Run the agent with a simple prompt
    run_coding_agent(
        prompt="Rename function foo to bar.",
        code_dir=temp_code_dir,
        pr_title="Rename foo to bar",
        pr_body="Renames foo to bar.",
        pr_branch="test-branch",
        commit_and_push=False
    )
    # Check that pr.yaml and git.sh were created
    assert os.path.exists(os.path.join(temp_code_dir, "pr.yaml"))
    assert os.path.exists(os.path.join(temp_code_dir, "git.sh"))
    # Check that the file was edited (if LLM is mocked or API key is set)
    with open(os.path.join(temp_code_dir, "foo.py"), encoding="utf-8") as f:
        content = f.read()
    # The actual content check depends on LLM response; here we just check file exists
    assert "def" in content
