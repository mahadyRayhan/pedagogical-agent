import requests

def reload_resources():
    try:
        response = requests.get('http://192.168.178.251:5000/reload_resource')
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()  # Parse the JSON response
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

def ask_question(query):
    try:
        response = requests.get("http://192.168.178.251:5000/ask", params={"query": query})
        response.raise_for_status()  # Raise an exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error occurred: {e}")
        return None

if __name__ == "__main__":
    while True:
        question = input("Enter your question (or type 'exit' to quit): ")

        if question.lower() == 'exit':
            print("Exiting the script.")
            break  # Exit the loop if the user types 'exit'

        response = ask_question(question)
        if response:
            print(response)
        else:
            print("No valid response received from the server.")