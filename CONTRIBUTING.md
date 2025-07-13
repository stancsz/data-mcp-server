# Contributing to mini

First off, thank you for considering contributing to mini! It’s people like you that make open source projects like this thrive.

## The Era of Vibe Coding

This project encourages a new way of working, which we call "Vibe Coding." In this paradigm, the focus shifts from writing code line-by-line to sharing ideas, guiding the AI agent, and influencing the project's direction. Your ability to articulate concepts, identify logical flaws, and collaborate on the overall architecture is more valuable than ever.

Here’s how you can contribute in this new era:

1.  **Join the Architecture Discussion:** Participate in discussions about the project's design and future direction. Your insights can help shape the agent's evolution.
2.  **Raise Issues on Logical Flaws:** If you spot a flaw in the agent's reasoning or the project's logic, open an issue. Your critical eye is essential for the project's integrity.
3.  **Report Bugs and Submit Logs:** When you encounter a bug, report it with as much detail as possible. Submitting logs from the agent's operations is incredibly helpful for debugging and improving the system.
4.  **Share Techniques and Agentic Designs:** If you have experience with other AI agents or have ideas for new agentic designs, share them! We are always looking to learn from other projects and incorporate new techniques.


## Where to Start

mini is an experimental project, and there are many ways to contribute. Whether you're a seasoned developer or just starting, your input is valuable. Here are a few areas where you can help:

### 1. Enhancing the Agent's Core Logic

The core of the agent lives in the `coding_agent/` directory. You can contribute by:
- Improving the planning and execution phases of the agent.
- Enhancing the self-reflection capabilities to generate more insightful logs.
- Optimizing the agent's interaction with the LLM.

### 2. Refining the Self-Learning Mechanism

The self-learning and self-evolving aspects are what make mini unique. You can contribute by:
- Improving the `self_learning_api.py` to handle more complex scenarios.
- Enhancing the logic that analyzes reflection logs and proposes self-edits.
- Exploring new ways for the agent to learn and evolve.

### 3. Expanding the Agent's Toolset

The agent's capabilities can be extended by giving it more tools to work with. You can contribute by:
- Integrating new tools for code analysis, such as linters or static analysis tools.
- Adding new capabilities, like the ability to interact with different APIs or services.
- Improving the existing Playwright integration for browser automation.

### 4. Improving the Prompts

The quality of the prompts used to interact with the LLM is crucial for the agent's performance. You can contribute by:
- Refining the existing prompts in the `coding_agent/` directory to be more effective.
- Creating new prompts for different tasks or scenarios.
- Experimenting with different prompting techniques to improve the agent's reasoning.

### 5. Strengthening the Testing Suite

Given that mini modifies its own code, a robust testing suite is essential. You can contribute by:
- Adding new unit tests for the agent's core logic in the `tests/` directory.
- Creating more complex scenarios in the `tests/dummy project/` to test the agent's capabilities.
- Adding integration tests to ensure that the different parts of the system work well together.

### 6. Improving the Documentation

Good documentation makes it easier for everyone to use and contribute to the project. You can contribute by:
- Improving the `README.md` file with more details or clearer explanations.
- Adding more examples of how to use the agent.
- Documenting the code with comments to make it easier to understand.

## How to Contribute

### Reporting Bugs

If you find a bug, please open an issue and provide as much information as possible, including:
- A clear and descriptive title.
- A detailed description of the bug and its behavior.
- Steps to reproduce the bug.
- Any relevant logs or error messages.

### Suggesting Enhancements

If you have an idea for an enhancement, please open an issue to discuss it. This allows us to coordinate our efforts and make sure your contribution aligns with the project's goals.

### Pull Requests

1. Fork the repository and create your branch from `main`.
2. Make your changes and ensure that the tests pass.
3. Open a pull request with a clear description of your changes.

## Code of Conduct

This project and everyone participating in it is governed by the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.
