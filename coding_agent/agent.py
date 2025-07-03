"""
Agent for autonomous code editing using OpenAI LLM.

Usage:
    from coding_agent.agent import run_coding_agent

    response_message, modified_files = run_coding_agent(
        prompt="Refactor this function to use async/await.",
        file_path="/path/to/file.py"
    )
    print(response_message)
    # modified_files is a list of file paths that were changed
"""

from openai import OpenAI
from .utils import read_file, write_file, file_diff

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
            "content": (
                "You are an expert software engineer AI. "
                "Given a user instruction and a code file, your first task is to create a clear, step-by-step plan for how you would accomplish the requested change. "
                "Do not write any code yet. Just output the plan as a numbered list."
            )
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
            "content": (
                "You are an autonomous coding agent. "
                "Given a user instruction, a step-by-step plan, and a code file, output the revised file content only. "
                "Do not include explanations or comments outside the code."
            )
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
