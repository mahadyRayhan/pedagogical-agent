from dotenv import load_dotenv
load_dotenv()  # Load environment variables early

import os
from flask import Flask, request, jsonify
from multi_agent_system.resource_manager import ResourceManager
from multi_agent_system.agent_coordinator import AgentCoordinator

# Optional: Check that the API key is loaded
if not os.getenv("GOOGLE_API_KEY"):
    raise Exception("GOOGLE_API_KEY is not set. Please check your .env file.")

app = Flask(__name__)

# Initialize resources and agent coordinator at startup
resource_manager = ResourceManager(resource_dir="uSucceed_resource")
resource_manager.load_resources()
coordinator = AgentCoordinator(resource_manager)

@app.route("/reload_resource", methods=["GET"])
def reload_resource():
    try:
        resource_manager.load_resources()
        return jsonify({"detail": "Resources reloaded successfully."}), 200
    except Exception as e:
        return jsonify({"detail": f"Failed to reload resources: {str(e)}"}), 500

@app.route("/ask", methods=["GET"])
def ask_question():
    query = request.args.get('query')
    if not query:
        return jsonify({"detail": "Query not provided"}), 400
    try:
        answer, timings = coordinator.route_query(query)
        return jsonify({"query": query, "answer": answer, "timings": timings}), 200
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

if __name__ == "__main__":
    # app.run(host="0.0.0.0", port=5000)
    app.run(host='127.0.0.1', port=5000)
