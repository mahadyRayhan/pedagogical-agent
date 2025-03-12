import re
import time
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

class BaseAgent:
    """
    Base class for AI agents. Handles common configuration,
    user name extraction, and query processing.
    """
    def __init__(self, resource_manager, user_cache: dict, agent_type: str):
        self.resource_manager = resource_manager
        self.user_cache = user_cache  # Shared cache (e.g., for user name)
        self.agent_type = agent_type
        self._configure_genai()

    def _configure_genai(self):
        """
        Configures the Gemini generative model with safety settings.
        """
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
        self.model = genai.GenerativeModel(
            model_name="gemini-1.5-flash", generation_config=generation_config
        )
        self.chat_session = self.model.start_chat()

    @staticmethod
    def extract_user_name(query: str) -> str:
        """
        Extracts a user name if the query contains an explicit name statement.
        """
        explicit_name_pattern = r"Hi, I am (\w+)|My name is (\w+)|Call me (\w+)"
        match = re.search(explicit_name_pattern, query, re.IGNORECASE)
        if match:
            return next(filter(None, match.groups()))
        return None

    def generate_prompt(self, query: str) -> str:
        """
        Abstract method to generate a context-aware prompt.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("generate_prompt must be implemented by the agent subclass.")

    def get_answer(self, query: str):
        """
        Processes the query by:
          - Checking/updating the user name.
          - Generating a context-specific prompt.
          - Building the history using relevant resources.
          - Sending the query to the Gemini chat session.
          - Caching and returning the answer along with execution timing.
        """
        timings = {}
        start_time = time.time()
        first_answer = ''

        # Check for explicit user name in the query
        old_user_name = self.user_cache.get("USER", "User")
        new_user_name = self.extract_user_name(query)
        if new_user_name and new_user_name.lower() != "user" and new_user_name != old_user_name:
            self.user_cache["USER"] = new_user_name
            pattern = r'(?<=[?.!])\s+'
            sentences = re.split(pattern, query)
            sentences = [sentence.strip() + (query[len(sentence):][0] if len(query) > len(sentence) else '') for sentence in sentences]
            remaining_query = sentences[-1] if len(sentences) > 1 else None
            print("Remaining query after name extraction:", remaining_query)
            if remaining_query is None:
                return (f"Hi! {new_user_name}. Thank you for sharing your name. I will use this for future reference.",
                    {"name_update": 0.0})
            else:
                first_answer = f"Hi! {new_user_name}. Thank you for sharing your name. I will use this for future reference."

        # Ensure resources are loaded
        if not self.resource_manager.loaded:
            raise Exception("Resources not loaded. Please load resources first using ResourceManager.load_resources().")

        # Generate prompt using specialized logic
        prompt = self.generate_prompt(query)
        user_name = self.user_cache.get("USER", "User")

        # Build history with relevant file information
        relevant_files = self.resource_manager.get_files_for_agent(self.agent_type)
        history = []
        for file in relevant_files:
            # For the LocationAgent, include full content from prioritized files.
            if self.agent_type == "location" and "Rooms_And_Tasks.pdf" in file.display_name:
                history.append({"role": "user", "parts": [file]})
            else:
                history.append({"role": "user", "parts": [f"Basic content from {file.display_name}"]})
        history.append({"role": "user", "parts": [prompt]})
        if self.agent_type == "location":
            self.chat_session.history = history

        # Send the prompt and measure response time.
        response_start = time.time()
        response = self.chat_session.send_message(prompt, safety_settings=self.safety_settings)
        timings["response_time"] = time.time() - response_start
        timings["total_time"] = time.time() - start_time

        # Cache and return the response.
        self.user_cache[query] = response.text
        
        if first_answer == '':
            final_response = first_answer + response.text
            return response.text, timings
        else:
            cleaned_response = re.sub(r"(?i)^hi\s+(" + self.user_cache.get("USER", "User") + "[!,:]?\s+)?", "", response.text).strip()
            final_response = f"{first_answer} {cleaned_response}".strip()
            
            return final_response, timings
