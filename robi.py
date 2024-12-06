
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
        answer = gemini_qa.get_answer(query)
        print(f"Generated Answer: {answer}")

if __name__ == "__main__":
    query="I am at 'Room 1'. what is my task here?"
    load_resource=True
    evaluation=False
    main(query, load_resource, evaluation)