from coding_agent import run_coding_agent

if __name__ == "__main__":
    # Example usage: edit code in ./my_project with a user prompt
    run_coding_agent(
        prompt="Refactor all functions to use async/await.",
        code_dir="./my_project",
        pr_title="Refactor to async/await",
        pr_body="This PR refactors all functions to use async/await syntax.",
        pr_branch="refactor-async-await",
        commit_and_push=True  # Set to True to commit and push changes
    )
