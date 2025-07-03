from flask import Flask, request, jsonify
import os
import subprocess

app = Flask(__name__)

@app.route('/self-learning', methods=['POST'])
def self_learning():
    """
    Receives self-learning payloads (reflection logs, self_edit_diffs).
    Applies code edits and commits/pushes via git.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "No JSON payload received"}), 400

    # Call the agent's self-learning logic to process the payload and edit the codebase
    try:
        from coding_agent.agent import agent_self_learn_from_payload
        modified_files = agent_self_learn_from_payload(data)
    except Exception as e:
        return jsonify({"error": f"Agent self-learning failed: {e}"}), 500

    if modified_files:
        # Commit and push changes
        commit_msg = data.get("commit_message", "Self-learning: applied reflection-based edits")
        try:
            subprocess.run(["git", "add", "."], check=True)
            subprocess.run(["git", "commit", "-m", commit_msg], check=True)
            subprocess.run(["git", "push"], check=True)
        except subprocess.CalledProcessError as e:
            return jsonify({"error": f"Git operation failed: {e}"}), 500

        return jsonify({"status": "Edits applied by agent, committed, and pushed.", "modified_files": modified_files}), 200

    return jsonify({"status": "Agent made no code changes."}), 200

if __name__ == "__main__":
    port = int(os.environ.get("SELF_LEARNING_API_PORT", 5000))
    app.run(host="0.0.0.0", port=port)
