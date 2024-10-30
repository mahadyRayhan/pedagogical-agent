
from Q_A import GeminiQuestion_and_Answering

def main(query, load_resource, evaluation):
    print("--------------------------------------------")
    print(query, load_resource, evaluation)
    print("--------------------------------------------")
    gemini_qa = GeminiQuestion_and_Answering()

    if load_resource:
        gemini_qa.load_resources(load_resource=load_resource)
    
    if evaluation:
        gemini_qa.evaluate()
    elif query:
        answer = gemini_qa.ask_question(query)
        print(f"Generated Answer: {answer}")

if __name__ == "__main__":
    query="What is a DDoS attack?"
    load_resource=True
    evaluation=False
    main(query, load_resource, evaluation)