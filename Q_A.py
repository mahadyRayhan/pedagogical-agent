import os
import time
import glob
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()

# Initialize GenAI with API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

class GeminiQuestion_and_Answering:
    def __init__(self):
        self.model = None
        self.safety_settings = None
        self.files = None
        self.chat_session = None
        self.cached_responses = {}

    def load_resources(self, load_resource=False):
        if load_resource or not self.files:
            file_paths = glob.glob("uSucceed_resource/*.pdf")
            self.files = self.upload_to_gemini(file_paths, mime_type="application/pdf")
            self.wait_for_files_active(self.files)
            self.configure_genai()

    def upload_to_gemini(self, paths, mime_type=None):
        files = []
        for path in paths:
            file = genai.upload_file(path, mime_type=mime_type)
            print(f"Uploaded file '{file.display_name}' as: {file.uri}")
            files.append(file)
        return files

    def wait_for_files_active(self, files):
        print("Waiting for file processing...")
        for name in (file.name for file in files):
            file = genai.get_file(name)
            while file.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(10)
                file = genai.get_file(name)
            if file.state.name != "ACTIVE":
                raise Exception(f"File {file.name} failed to process")
        print("...all files ready\n")

    def configure_genai(self):
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
        }
        generation_config = {
            "temperature": 0,
            "top_p": 0.95,
            "top_k": 64,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        self.model = genai.GenerativeModel(model_name="gemini-1.5-flash", generation_config=generation_config)
        self.chat_session = self.model.start_chat()

    def detect_query_type(self, query: str) -> str:
        """Detect query type for document prioritization"""
        location_keywords = ['room', 'location', 'where', 'place', 'area', 'task']
        security_keywords = ['security', 'cyber', 'attack', 'threat', 'protection']
        system_keywords = ['controller', 'system', 'asset', 'configuration']
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in location_keywords):
            return 'location'
        elif any(keyword in query_lower for keyword in security_keywords):
            return 'cybersecurity'
        elif any(keyword in query_lower for keyword in system_keywords):
            return 'system'
        return 'other'

    def get_answer(self, query: str):
        """Process query and generate answer using loaded files, returning the answer and execution times for each part."""
        timings = {}
        start_time = time.time()

        try:
            # Get loaded files
            if not self.files:
                raise Exception("No files loaded. Please load files first using load_files()")
            
            timings['initial_check'] = time.time() - start_time  # Time for initial file check
            
            # Check cache first to save time on repeated queries
            if query in self.cached_responses:
                return self.cached_responses[query], {'cached': True, 'total_time': time.time() - start_time}

            # Prepare chat context and prompt
            query_type = self.detect_query_type(query)
            prompt_intro = "You are a question answering model. Please answer the following question briefly and to the point. If there are multiple points found, give them all as it is and list them in a list. The question is:"
            prompt = prompt_intro + " " + query
            
            # Prioritize relevant files for location queries
            relevant_files_start_time = time.time()
            relevant_files = self.files

            # Separate and prioritize files based on query type
            if query_type == 'location':
                prioritized_files = [file for file in self.files if 'Rooms_And_Tasks.pdf' in file.display_name]
                other_files = [file for file in self.files if 'Rooms_And_Tasks.pdf' not in file.display_name]
                relevant_files = prioritized_files + other_files
                
            timings['relevant_files_selection'] = time.time() - relevant_files_start_time  # Time for file selection
            
            # Optimize the history update to keep full content only in prioritized files
            history = []
            for file in relevant_files:
                if query_type == 'location' and 'Rooms_And_Tasks.pdf' in file.display_name:
                    history.append({
                        "role": "user",
                        "parts": [file]  # Full content for prioritized files
                    })
                else:
                    # Use minimal info for other files
                    history.append({
                        "role": "user",
                        "parts": [f"Basic content from {file.display_name}"]
                    })
            
            # Add prompt to history
            history.append({
                "role": "user",
                "parts": [prompt]
            })
            
            # Apply history if this is a location query or complex question
            if query_type == 'location':
                self.chat_session.history = history
            
            # Get response from chat session
            response_start_time = time.time()
            # response = chat_session.send_message(prompt)
            response = self.chat_session.send_message(prompt, safety_settings=self.safety_settings)
            
            end_time = time.time()
            timings['response_time'] = end_time - response_start_time  # Time for getting response
            timings['total_time'] = end_time - start_time  # Total time taken
            
            # Cache the response
            self.cached_responses[query] = response.text
            
            return response.text, timings  # Return answer and timing breakdown
            
        except Exception as e:
            end_time = time.time()
            print(f"\nError occurred after {end_time - start_time:.2f} seconds")
            print(f"Error processing query: {str(e)}")
            return f"An error occurred: {str(e)}", timings  # Return the error and timings
        
# Main function to handle querying and evaluation
def gemini_qa_system(query="", load_resource=True, evaluate=True):
    gemini_qa = GeminiQuestion_and_Answering()

    if load_resource:
        gemini_qa.load_resources(load_resource=True)
    
    if evaluate:
        gemini_qa.evaluate()
    elif query:
        answer = gemini_qa.get_answer(query)
        print(f"Generated Answer: {answer}")