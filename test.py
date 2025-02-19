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
    
   questions = [
    "What is a DDoS attack?",
    "I am at room 1, what should I do?",
    "What is 5+5?",
    "What is DNS?",
    "Is earth flat?",
    "What is the capital of USA?",
    "Who killed JFK?",
    "I am at 'Room 1'. What is my task here?",
    "What is Phishing?",
    "What are cybersecurity best practices?",
    "What is IoT?",  # No answer. Resource just has the word IoT but does not mention what it is.
    "What is cybersecurity?",
    "What is Integrity?",
    "What is VPN?",
    "What quality security system includes?",
    "What is Malware?",
    "I am at room 4, what should I do?",
    "Hi, I am Jack. Remember my name, and from now on use this name to mention me if necessary.",
    "I am at 'Room 1'. What is my task here?",
    "Call me Sarah.",
    "What is a spoofing attack?",
    "Can you call me Noah moving forward?",
    "Who are you?",
    "How can I move forward?",
    "How can I summon Robi?",
    "How can I handle an object?",
    "How can I move?",
    "How can I grab things?",
    "Do I just bend and press a button to pick up an object?",
    "How do I interact with a canvas/UI?",
    "How do I click on icons in the UI?",
    "I'm playing the icon-matching game and I'm trying to grab icons. How can I do so?",
    "where am i, roomname: room3",
    "where am i, roomname: room2"
]

for question in questions:
    response = ask_question(question)
    if response:
        answer_text = response['answer'][0] if isinstance(response['answer'], list) else response['answer']
        query = response.get('query', question)
        metadata = response['answer'][1] if isinstance(response['answer'], list) and isinstance(response['answer'][1], dict) else {}

        print(f"Q: {query}\nA: {answer_text.strip()}\n")
        
        if metadata:
            print("⏳ Response Metadata:")
            for key, value in metadata.items():
                print(f"   - {key.replace('_', ' ').capitalize()}: {value:.4f}")
        
        print("\n" + "="*50 + "\n")  # Separator for readability