import os
import tempfile
import pytest
import logging
import sys

# Configure logging to print all messages to stdout
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s:%(message)s",
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

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

def test_run_coding_agent_modify_dummy_project():
    dummy_file = os.path.join("tests", "dummy project", "app.py")
    # Backup the original content
    import tempfile
    with open(dummy_file, encoding="utf-8") as f:
        original_content = f.read()
    # Save original content to a temp file for later diff
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as tmp_orig:
        tmp_orig.write(original_content)
        tmp_orig_path = tmp_orig.name
    try:
        response_message, modified_files = run_coding_agent(
            prompt="Add a comment '# Modified by agent test' at the top of the file.",
            file_path=dummy_file
        )
        with open(dummy_file, encoding="utf-8") as f:
            content = f.read()
        assert content.startswith("# Modified by agent test")
        assert dummy_file in modified_files
        assert "Step-by-step plan" in response_message
        assert "Summary of changes" in response_message
    finally:
        # After test, copy the dummy project to a timestamped __test__ directory
        import shutil
        from datetime import datetime
        src_dir = os.path.join("tests", "dummy project")
        timestamp = datetime.now().strftime("%y%m%d%H%M%S")
        dst_dir = os.path.join("tests", f"dummy project__{timestamp}__test__")
        shutil.copytree(src_dir, dst_dir)
        # Compare the original (from temp file) and test copy, print diff lines or "no change"
        import difflib
        test_file = os.path.join(dst_dir, "app.py")
        with open(tmp_orig_path, encoding="utf-8") as f1, open(test_file, encoding="utf-8") as f2:
            orig_content = f1.readlines()
            test_content = f2.readlines()
        diff = list(difflib.unified_diff(orig_content, test_content, fromfile="original_app.py", tofile=test_file))
        if diff:
            logger.info("".join(diff))
        else:
            logger.info("no change")
        # Restore the original content
        with open(dummy_file, "w", encoding="utf-8") as f:
            f.write(original_content)
