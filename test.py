import requests

def reload_resources():
    try:
        response = requests.get('http://127.0.0.1:5000/reload_resource')
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # Parse the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None
    
def ask_question(query):
    try: #http://127.0.0.1:5000
        response = requests.get("http://127.0.0.1:5000/ask", params={"query": query})
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None
if __name__ == "__main__":
    
    # result = reload_resources()
    # if result:
    #     print(result)
    
    question = "What is a DDoS attack?"
    question = "I am at room 1, what should I do?"
    # question = "what is 5+5?"
    # question = "what is DNS?"
    # question = "is earth flat?"
    # question = "what is the capital of USA?"
    # question = "who killed JFK?"
    # question = "I am at 'Room 1'. what is my task here?"
    # question = "What is Phishing?"
    # question = "What are cybersecurity best practices?"
    # question = "What is IoT?"
    # question = "Hi"
    # Query to set the name
    question = "I am at room 1, what should I do?"
    # question = "Hi, I am Jack. Remember my name, and now on use this name to mention me if necessary."
    response = ask_question(question)
    if response:
        print(response)
