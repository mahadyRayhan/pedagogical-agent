from flask import Flask, request, jsonify
from Q_A import GeminiQuestion_and_Answering

app = Flask(__name__)

# Initialize the GeminiQuestion_and_Answering system at startup
gemini_qa = GeminiQuestion_and_Answering()
gemini_qa.load_resources(load_resource=True)

@app.route("/reload_resource", methods=["GET"])
def reload_resource():
    try:
        gemini_qa.load_resources(load_resource=True)  # Reload the resources
        return jsonify({"detail": "Resources reloaded successfully."}), 200
    except Exception as e:
        return jsonify({"detail": f"Failed to reload resources: {str(e)}"}), 500

@app.route("/ask", methods=["GET"])
def ask_question():
    query = request.args.get('query')
    if not query:
        return jsonify({"detail": "Query not provided"}), 400
    try:
        answer = gemini_qa.get_answer(query)
        return jsonify({"query": query, "answer": answer}), 200
    except Exception as e:
        return jsonify({"detail": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)