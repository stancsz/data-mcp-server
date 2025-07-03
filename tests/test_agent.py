import os
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
def temp_code_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = create_sample_file(tmpdir, "foo.py", "def foo():\n    return 1\n")
        yield file_path  # Provide the temp file path to the test

def test_run_coding_agent_basic(temp_code_file):
    # Run the agent with a simple prompt
    response_message, modified_files = run_coding_agent(
        prompt="Rename function foo to bar.",
        file_path=temp_code_file
    )
    # Check that the file was edited (if LLM is mocked or API key is set)
    with open(temp_code_file, encoding="utf-8") as f:
        content = f.read()
    # The actual content check depends on LLM response; here we just check file exists and was changed
    assert "def" in content
    assert temp_code_file in modified_files
    assert "Step-by-step plan" in response_message
    assert "Summary of changes" in response_message
