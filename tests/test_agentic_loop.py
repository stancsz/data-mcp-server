import os
import tempfile
import json
import pytest

from coding_agent.agent import Task

def create_sample_file(dir_path, filename, content):
    file_path = os.path.join(dir_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path

class DummyLLMResponse:
    def __init__(self, output_text):
        self.output_text = output_text

class DummyOpenAIClient:
    """Simulates OpenAI client for agentic loop tests."""
    def __init__(self, outputs):
        self.outputs = outputs
        self.call_count = 0
    class responses:
        @staticmethod
        def create(*args, **kwargs):
            # This will be replaced in __init__
            pass
    def patch(self):
        # Patch the responses.create method to use our outputs
        def create(*args, **kwargs):
            idx = self.call_count
            self.call_count += 1
            if idx < len(self.outputs):
                return DummyLLMResponse(self.outputs[idx])
            # Default: always return <attempt_completion> after outputs exhausted
            return DummyLLMResponse("<attempt_completion>Task done</attempt_completion>")
        self.responses.create = create

@pytest.fixture
def temp_code_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = create_sample_file(tmpdir, "foo.py", "def foo():\n    return 1\n")
        yield file_path

def test_agentic_loop_prompt_flow(monkeypatch, temp_code_file):
    """Test Task agentic loop completes and modifies file as expected."""
    # Simulate LLM: plan, then write_file, then attempt_completion
    outputs = [
        "1. Rename function foo to bar.",  # plan
        "<write_file><content>def bar():\n    return 1\n</content></write_file>",
        "<attempt_completion>Task done</attempt_completion>"
    ]
    dummy_client = DummyOpenAIClient(outputs)
    dummy_client.patch()
    monkeypatch.setattr("coding_agent.agent.OpenAI", lambda: dummy_client)

    task = Task(
        user_instruction="Rename function foo to bar.",
        file_path=temp_code_file,
        max_loops=5
    )
    task.start()
    # Check plan, completion, file modification, and status
    assert "Rename function foo to bar" in task.plan
    assert "<attempt_completion>" in (task.completion or "")
    with open(temp_code_file, encoding="utf-8") as f:
        content = f.read()
    assert "def bar()" in content
    assert "completed successfully" in task.status_message

def test_agentic_loop_max_loops_reflection(monkeypatch, temp_code_file):
    """Test Task agentic loop hits max_loops and triggers reflection log."""
    # Simulate LLM: plan, then always write_file (never attempt_completion)
    outputs = [
        "1. Do nothing."  # plan
    ] + [
        "<write_file><content>def foo():\n    return 1\n</content></write_file>"
    ] * 7  # more than max_loops
    dummy_client = DummyOpenAIClient(outputs)
    dummy_client.patch()
    monkeypatch.setattr("coding_agent.agent.OpenAI", lambda: dummy_client)

    task = Task(
        user_instruction="Do nothing.",
        file_path=temp_code_file,
        max_loops=5
    )
    # Remove any pre-existing reflection logs
    for f in os.listdir():
        if f.startswith("reflection log"):
            os.remove(f)
    task.start()
    # Should exit due to max_loops
    assert "max_loops" in task.status_message
    # Check that a reflection log file was created in log/
    log_dir = "log"
    logs = []
    if os.path.exists(log_dir):
        logs = [f for f in os.listdir(log_dir) if f.startswith("reflection log")]
    assert logs, "No reflection log generated"
    # Optionally, check contents of the log
    with open(os.path.join(log_dir, logs[0]), encoding="utf-8") as f:
        log = json.load(f)
    assert log["loop_count"] == 5
    assert log["status_message"].startswith("Agentic loop exited after reaching max_loops")
