from flask import Flask, request, jsonify
import requests
import os
from flask_cors import CORS
from services.agent_creator import AgentCreator
# print(AgentCreator.create_retell_agent_with_llm)
app = Flask(__name__)
CORS(app)

@app.route("/create-agent", methods=["POST"])
def create_agent():
    data = request.json
    if not data or "provider" not in data:
        return jsonify({"error": "Invalid request, Provider must be specified (vapi or retail)"}), 400

    provider = data["provider"]
    agent_data = data.get("agent_data", {})

    try:
        if provider == "vapi":
            result, status_code = AgentCreator.create_vapi_agent(agent_data)
        elif provider == "retell":
            result, status_code = AgentCreator.create_retell_agent_with_llm(agent_data)
        else:
            return jsonify({"error": "Invalid provider"}), 400
        
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)