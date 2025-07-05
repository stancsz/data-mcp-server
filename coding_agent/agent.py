"""
Agent for autonomous code editing using OpenAI LLM.

Usage:
    from coding_agent.agent import run_coding_agent, Task

    # Simple one-shot agent
    response_message, modified_files = run_coding_agent(
        prompt="Refactor this function to use async/await.",
        file_path="/path/to/file.py"
    )
    print(response_message)
    # modified_files is a list of file paths that were changed

    # Full agentic loop
    task = Task(
        user_instruction="Refactor this function to use async/await.",
        file_path="/path/to/file.py"
    )
    task.start()
    print(task.get_summary())
"""

import os
from openai import OpenAI
from .utils import read_file, write_file, file_diff

def build_system_prompt(phase="plan", tools=None, extra_instructions=None, env_details=None):
    """
    Build a system prompt describing the agent, available tools, and rules.
    phase: "plan" or "execute" or "loop"
    """
    cwd = os.getcwd()
    persona = (
        "You are an expert coding agent. "
        "You can read, write, and diff code files using XML-formatted tool calls. "
        "You work step-by-step, using one tool per message, and always wait for the result before proceeding."
    )
    if tools is None:
        tools = """
# Tools

## read_file
Description: Read the contents of a file.
Parameters:
- path: (required) The path to the file.
Usage:
<read_file>
<path>path/to/file.py</path>
</read_file>

## write_file
Description: Write content to a file (overwrites if exists).
Parameters:
- path: (required) The path to the file.
- content: (required) The content to write.
Usage:
<write_file>
<path>path/to/file.py</path>
<content>
...file content here...
</content>
</write_file>

## file_diff
Description: Show a unified diff between two versions of a file.
Parameters:
- before: (required) The original file content.
- after: (required) The new file content.
- path: (required) The file path.
Usage:
<file_diff>
<before>old content</before>
<after>new content</after>
<path>path/to/file.py</path>
</file_diff>
"""
    guidelines = """
# Tool Use Guidelines
- Use one tool per message, and wait for the result before continuing.
- Always use XML tags as shown above.
- Do not output explanations outside of tool calls unless asked.
- If you are planning, only output a numbered list of steps.
- If you are editing, only output the revised file content.
"""
    if env_details is None:
        env_details = f"""
# Environment Details
- OS: {os.name}
- Current Working Directory: {cwd}
"""
    if phase == "plan":
        instructions = (
            "Your first task is to create a clear, step-by-step plan for how you would accomplish the requested change. "
            "Do not write any code yet. Just output the plan as a numbered list."
        )
    elif phase == "execute":
        instructions = (
            "Given a user instruction, a step-by-step plan, and a code file, output the revised file content only. "
            "Do not include explanations or comments outside the code."
        )
    else:
        instructions = (
            "You are in an agentic loop. For each step, decide whether to use a tool or call attempt_completion. "
            "If you use a tool, output only the tool call in XML. Wait for the result before continuing. "
            "If you are done, call attempt_completion."
        )
    prompt = f"""{persona}
{tools}
{guidelines}
{env_details}
# Instructions
{instructions}
"""
    if extra_instructions:
        prompt += f"\n# Extra Instructions\n{extra_instructions}\n"
    return prompt

def agent_self_learn_from_payload(payload):
    """
    Self-learning entrypoint: Given a reflection log or self_edit_diffs payload,
    use the agent's own logic to analyze and edit the codebase.
    """
    # If self_edit_diffs are present, treat as a suggestion to review those files
    # If a reflection log is present, use its info to guide edits
    from openai import OpenAI
    import json

    client = OpenAI()
    modified_files = []

    # Try to extract a user_instruction and plan from the payload
    user_instruction = payload.get("user_instruction") or "Improve the codebase based on the following reflection log."
    plan = payload.get("plan")
    file_path = payload.get("file_path") or None

    # If self_edit_diffs are present, review those files
    self_edit_diffs = payload.get("self_edit_diffs")
    files_to_review = []
    if self_edit_diffs:
        files_to_review = [entry.get("file") for entry in self_edit_diffs if entry.get("file")]

    # If no files specified, review all agent code files
    if not files_to_review:
        files_to_review = [
            "example.py",
            "coding_agent/__init__.py",
            "coding_agent/agent.py",
            "coding_agent/mcp.py",
            "coding_agent/utils.py",
            "tests/test_agent.py"
        ]

    # For each file, run the agent logic to improve it based on the payload
    for path in files_to_review:
        try:
            with open(path, "r", encoding="utf-8") as f:
                file_content = f.read()
            # Compose a prompt for the agent
            prompt = (
                f"{user_instruction}\n"
                f"Reflection log (if any):\n{json.dumps(payload, indent=2)}\n"
                f"File path: {path}\n"
                f"File content:\n{file_content}\n"
            )
            # Use the agent's LLM to suggest improvements
            planning_input = [
                {
                    "role": "system",
                    "content": build_system_prompt(phase="plan")
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
            plan_response = client.responses.create(
                model="gpt-4.1",
                input=planning_input,
                text={"format": {"type": "text"}},
                reasoning={},
                tools=[],
                temperature=0.5,
                max_output_tokens=512,
                top_p=1,
                store=True
            )
            plan_text = getattr(plan_response, "output_text", "").strip()

            # Execution phase: ask LLM to edit the file according to the plan
            execution_input = [
                {
                    "role": "system",
                    "content": build_system_prompt(phase="execute")
                },
                {
                    "role": "user",
                    "content": (
                        f"User instruction: {user_instruction}\n"
                        f"Step-by-step plan:\n{plan_text}\n"
                        f"File path: {path}\n"
                        f"File content:\n{file_content}"
                    )
                }
            ]
            exec_response = client.responses.create(
                model="gpt-4.1",
                input=execution_input,
                text={"format": {"type": "text"}},
                reasoning={},
                tools=[],
                temperature=0.7,
                max_output_tokens=2048,
                top_p=1,
                store=True
            )
            after = getattr(exec_response, "output_text", "").strip()
            if after and after != file_content:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(after)
                modified_files.append(path)
        except Exception as e:
            print(f"Self-learning: failed to process {path}: {e}")

    return modified_files

def run_coding_agent(prompt, file_path):
    """
    Main entrypoint for the coding agent.

    Args:
        prompt (str): User instruction for code changes.
        file_path (str): Path to the code file to edit.

    Returns:
        response_message (str): The plan and summary of changes.
        modified_files (list): List of file paths that were changed.
    """
    client = OpenAI()
    modified_files = []

    # 1. Planning phase: ask LLM for a step-by-step plan
    planning_input = [
        {
            "role": "system",
            "content": build_system_prompt(phase="plan")
        },
        {
            "role": "user",
            "content": (
                f"User instruction: {prompt}\n"
                f"File path: {file_path}\n"
                f"File content:\n{read_file(file_path)}"
            )
        }
    ]
    plan_response = client.responses.create(
        model="gpt-4.1",
        input=planning_input,
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[],
        temperature=0.5,
        max_output_tokens=512,
        top_p=1,
        store=True
    )
    plan = getattr(plan_response, "output_text", "").strip()

    # 2. Execution phase: ask LLM to edit the file according to the plan
    before = read_file(file_path)
    execution_input = [
        {
            "role": "system",
            "content": build_system_prompt(phase="execute")
        },
        {
            "role": "user",
            "content": (
                f"User instruction: {prompt}\n"
                f"Step-by-step plan:\n{plan}\n"
                f"File path: {file_path}\n"
                f"File content:\n{before}"
            )
        }
    ]
    exec_response = client.responses.create(
        model="gpt-4.1",
        input=execution_input,
        text={"format": {"type": "text"}},
        reasoning={},
        tools=[],
        temperature=0.7,
        max_output_tokens=2048,
        top_p=1,
        store=True
    )
    after = getattr(exec_response, "output_text", "").strip()

    # 3. Write the new file if changed
    if after and after != before:
        write_file(file_path, after)
        modified_files.append(file_path)
        diff = file_diff(before, after, file_path)
    else:
        diff = "No changes made."

    # 4. Compose response message
    response_message = (
        "Step-by-step plan:\n"
        f"{plan}\n\n"
        "Summary of changes:\n"
        f"{diff}"
    )

    return response_message, modified_files

class Task:
    """
    Task class for managing the agentic loop and prompt flow.
    """
    def __init__(self, user_instruction, file_path, model="gpt-4.1", max_loops=10):
        self.user_instruction = user_instruction
        self.file_path = file_path
        self.model = model
        self.max_loops = max_loops
        self.client = OpenAI()
        self.conversation = []
        self.modified_files = []
        self.plan = None
        self.completion = None
        self.finished = False
        self.loop_count = 0
        self.status_message = ""

    def start(self):
        """
        Start the agentic loop for this task.
        """
        # Step 1: Planning
        self._add_message("system", build_system_prompt(phase="plan"))
        self._add_message("user", (
            f"User instruction: {self.user_instruction}\n"
            f"File path: {self.file_path}\n"
            f"File content:\n{read_file(self.file_path)}"
        ))
        plan_response = self.client.responses.create(
            model=self.model,
            input=self.conversation,
            text={"format": {"type": "text"}},
            reasoning={},
            tools=[],
            temperature=0.5,
            max_output_tokens=512,
            top_p=1,
            store=True
        )
        self.plan = getattr(plan_response, "output_text", "").strip()
        self.conversation = []  # Reset for agentic loop

        # Step 2: Agentic Loop
        user_content = (
            f"User instruction: {self.user_instruction}\n"
            f"Step-by-step plan:\n{self.plan}\n"
            f"File path: {self.file_path}\n"
            f"File content:\n{read_file(self.file_path)}"
        )
        self._add_message("system", build_system_prompt(phase="loop"))
        self._add_message("user", user_content)

        self.loop_count = 0
        self.finished = False
        self.completion = None
        self.status_message = ""

        while not self.finished and self.loop_count < self.max_loops:
            self.loop_count += 1
            response = self.client.responses.create(
                model=self.model,
                input=self.conversation,
                text={"format": {"type": "text"}},
                reasoning={},
                tools=[],
                temperature=0.7,
                max_output_tokens=2048,
                top_p=1,
                store=True
            )
            output = getattr(response, "output_text", "").strip()
            if output.startswith("<attempt_completion>"):
                self.completion = output
                self.finished = True
                self.status_message = f"Task completed successfully in {self.loop_count} loop(s)."
            elif output.startswith("<write_file>"):
                # Parse XML for path/content (simple extraction)
                path = self.file_path
                content = self._extract_tag(output, "content")
                before = read_file(path)
                write_file(path, content)
                self.modified_files.append(path)
                diff = file_diff(before, content, path)
                tool_result = f"<file_diff>\n{diff}\n</file_diff>"
                self._add_message("assistant", output)
                self._add_message("tool", tool_result)
            elif output.startswith("<read_file>"):
                path = self.file_path
                content = read_file(path)
                tool_result = f"<read_file>\n{content}\n</read_file>"
                self._add_message("assistant", output)
                self._add_message("tool", tool_result)
            else:
                # Unknown or unsupported tool, or plain text
                self._add_message("assistant", output)
                self.finished = True
                self.status_message = (
                    f"Agentic loop exited after {self.loop_count} loop(s) without explicit completion."
                )

        if not self.finished and self.loop_count >= self.max_loops:
            self.status_message = (
                f"Agentic loop exited after reaching max_loops={self.max_loops} without explicit completion."
            )
            self._reflect_and_log()
            self.finished = True

    def _add_message(self, role, content):
        self.conversation.append({"role": role, "content": content})

    def _extract_tag(self, xml, tag):
        # Simple XML tag extraction (not robust, for demo purposes)
        import re
        match = re.search(f"<{tag}>(.*?)</{tag}>", xml, re.DOTALL)
        return match.group(1).strip() if match else ""

    def _reflect_and_log(self):
        """
        Reflection mechanism: log thoughts, loop, and possible cause when max_loops is reached.
        Generates a JSON file and (optionally) sends it to the agent's 'brain'.
        """
        import json
        import datetime
        import re

        # Brief error message for filename
        brief_error = re.sub(r'[^a-zA-Z0-9_ -]', '', self.status_message)[:40].replace(' ', '_')
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        log_dir = "log"
        os.makedirs(log_dir, exist_ok=True)
        filename = os.path.join(log_dir, f"reflection log - {brief_error}_{timestamp}.json")

        # Gather thoughts (all conversation history)
        thoughts = self.conversation

        # Reflection: simple heuristic for now
        possible_cause = "The agent reached the maximum number of loops without completing the task. This may be due to ambiguous instructions, insufficient tool use, or a bug in the code editing logic."

        reflection_log = {
            "timestamp": timestamp,
            "user_instruction": self.user_instruction,
            "file_path": self.file_path,
            "plan": self.plan,
            "loop_count": self.loop_count,
            "max_loops": self.max_loops,
            "status_message": self.status_message,
            "thoughts": thoughts,
            "possible_cause": possible_cause,
        }

        # Write JSON file
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(reflection_log, f, indent=2)

        # Check for self-learning integration
        enable_self_learning = os.environ.get("ENABLE_SELF_LEARNING", "false").lower() == "true"
        self_learning_url = os.environ.get("AGENT_SELF_LEARNING_URL")
        if enable_self_learning and self_learning_url:
            try:
                import requests
                resp = requests.post(self_learning_url, json=reflection_log, timeout=10)
                print(f"Reflection log sent to self-learning endpoint: {resp.status_code}")
            except Exception as e:
                print(f"Failed to send reflection log to self-learning endpoint: {e}")

        # Self-editing: Analyze repo for insufficient code and self-edit, then send diff to self-learning endpoint
        # Only proceed if self-learning is enabled and self_learning_url is set
        if enable_self_learning and self_learning_url:
            python_files = [
                "example.py",
                "coding_agent/__init__.py",
                "coding_agent/agent.py",
                "coding_agent/mcp.py",
                "coding_agent/utils.py",
                "tests/test_agent.py"
            ]
            diffs = []
            for file_path in python_files:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        before = f.read()
                    # Placeholder: Use LLM to suggest edit based on reflection_log and file content
                    # For now, just pass through the original content (no edit)
                    after = before
                    # TODO: Integrate LLM call here to suggest improvements
                    if after != before:
                        with open(file_path, "w", encoding="utf-8") as f:
                            f.write(after)
                        # Use file_diff utility if available
                        try:
                            diff = file_diff(before, after, file_path)
                        except Exception:
                            diff = f"Diff for {file_path} not available."
                        diffs.append({"file": file_path, "diff": diff})
                except Exception as e:
                    diffs.append({"file": file_path, "error": str(e)})
            # Send diffs to self-learning endpoint if any changes were made
            if diffs:
                try:
                    resp = requests.post(self_learning_url, json={"self_edit_diffs": diffs}, timeout=10)
                    print(f"Self-edit diffs sent to self-learning endpoint: {resp.status_code}")
                except Exception as e:
                    print(f"Failed to send self-edit diffs to self-learning endpoint: {e}")

    def get_summary(self):
        summary = "Step-by-step plan:\n"
        summary += f"{self.plan}\n\n"
        if self.completion:
            summary += f"Completion:\n{self.completion}\n"
        if self.modified_files:
            summary += f"Modified files: {self.modified_files}\n"
        summary += f"Status: {self.status_message}\n"
        return summary
