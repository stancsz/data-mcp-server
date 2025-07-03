import os
import tempfile
import json
import pytest

from coding_agent.agent import agent_self_learn_from_payload

def create_sample_file(dir_path, filename, content):
    file_path = os.path.join(dir_path, filename)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path

def test_agent_self_learn_from_payload_edits_file(tmp_path, monkeypatch):
    """Test that agent_self_learn_from_payload edits files based on payload."""
    # Create a sample file to be edited
    file_path = create_sample_file(tmp_path, "foo.py", "def foo():\n    return 1\n")
    payload = {
        "user_instruction": "Rename function foo to bar.",
        "file_path": str(file_path),
        "plan": "1. Rename foo to bar.",
        "self_edit_diffs": [{"file": str(file_path)}]
    }
    # Patch OpenAI client to simulate LLM output
    class DummyLLMResponse:
        def __init__(self, output_text):
            self.output_text = output_text
    class DummyOpenAIClient:
        def __init__(self):
            self.call_count = 0
        class responses:
            @staticmethod
            def create(*args, **kwargs):
                # Always return a plan or new file content
                if "plan" in args[0][1]["content"]:
                    return DummyLLMResponse("1. Rename foo to bar.")
                return DummyLLMResponse("def bar():\n    return 1\n")
    monkeypatch.setattr("coding_agent.agent.OpenAI", lambda: DummyOpenAIClient())
    modified = agent_self_learn_from_payload(payload)
    # Check that the file was edited
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    assert "def bar()" in content
    assert str(file_path) in modified

def test_reflection_log_post(monkeypatch, tmp_path):
    """Test that a reflection log is POSTed to the self-learning API if configured."""
    # Simulate requests.post and check call
    called = {}
    def dummy_post(url, json, timeout):
        called["url"] = url
        called["json"] = json
        called["timeout"] = timeout
        class DummyResp:
            status_code = 200
        return DummyResp()
    monkeypatch.setattr("requests.post", dummy_post)
    # Set env var for self-learning URL
    os.environ["AGENT_SELF_LEARNING_URL"] = "http://dummy/self-learning"
    # Import Task here to pick up monkeypatch
    from coding_agent.agent import Task
    # Create a dummy file
    file_path = tmp_path / "foo.py"
    file_path.write_text("def foo():\n    return 1\n")
    # Patch OpenAI to always return <write_file> (never completes)
    class DummyLLMResponse:
        def __init__(self, output_text):
            self.output_text = output_text
    class DummyOpenAIClient:
        def __init__(self):
            self.call_count = 0
        class responses:
            @staticmethod
            def create(*args, **kwargs):
                if "plan" in args[0][1]["content"]:
                    return DummyLLMResponse("1. Do nothing.")
                return DummyLLMResponse("<write_file><content>def foo():\n    return 1\n</content></write_file>")
    monkeypatch.setattr("coding_agent.agent.OpenAI", lambda: DummyOpenAIClient())
    # Remove any pre-existing reflection logs
    for f in os.listdir():
        if f.startswith("reflection log"):
            os.remove(f)
    task = Task(
        user_instruction="Do nothing.",
        file_path=str(file_path),
        max_loops=2
    )
    task.start()
    # Should have called requests.post
    assert "url" in called
    assert called["url"] == "http://dummy/self-learning"
    assert "reflection log" in called["json"]["status_message"]

def test_self_learning_api_endpoint(monkeypatch):
    """Test the /self-learning API endpoint accepts POST and triggers self-learning."""
    # Patch agent_self_learn_from_payload to record call
    called = {}
    def dummy_learn(payload):
        called["payload"] = payload
        return ["foo.py"]
    monkeypatch.setattr("coding_agent.agent.agent_self_learn_from_payload", dummy_learn)
    # Import Flask app
    import self_learning_api
    app = self_learning_api.app
    client = app.test_client()
    payload = {"user_instruction": "Improve code."}
    resp = client.post("/self-learning", json=payload)
    assert resp.status_code == 200
    assert "foo.py" in resp.get_json().get("modified_files", [])
    assert called["payload"]["user_instruction"] == "Improve code."
