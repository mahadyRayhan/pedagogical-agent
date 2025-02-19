import os
import re
import time
import glob
import PyPDF2
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

load_dotenv()

# Initialize GenAI with API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))


#########################################
# Resource Manager
#########################################

class ResourceManager:
    """
    Manages loading and uploading of PDF resources.
    """
    def __init__(self, resource_dir="uSucceed_resource"):
        self.resource_dir = resource_dir
        self.files = []  # List of uploaded file objects from Gemini
        self.nav_guide = ""  # Content from the NAVIGATION_control.pdf file
        self.loaded = False

    def load_resources(self):
        """
        Loads all PDF files from the resource directory, uploads them to Gemini,
        and caches the navigation guide separately.
        """
        file_paths = glob.glob(os.path.join(self.resource_dir, "*.pdf"))
        self.files = []
        for path in file_paths:
            file_obj = genai.upload_file(path, mime_type="application/pdf")
            print(f"Uploaded file '{file_obj.display_name}' as: {file_obj.uri}")
            self.files.append(file_obj)

        self.wait_for_files_active(self.files)
        self._load_navigation_guide()
        self.loaded = True

    def wait_for_files_active(self, files):
        """
        Waits until each file is processed (state ACTIVE) by Gemini.
        """
        print("Waiting for file processing...")
        for file in files:
            file_obj = genai.get_file(file.name)
            while file_obj.state.name == "PROCESSING":
                print(".", end="", flush=True)
                time.sleep(10)
                file_obj = genai.get_file(file.name)
            if file_obj.state.name != "ACTIVE":
                raise Exception(f"File {file_obj.name} failed to process")
        print("\n...all files ready\n")

    def _load_navigation_guide(self):
        """
        Reads and caches the navigation guide from NAVIGATION_control.pdf.
        """
        nav_path = os.path.join(self.resource_dir, "NAVIGATION_control.pdf")
        if os.path.exists(nav_path):
            with open(nav_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                pages = [page.extract_text() for page in reader.pages]
                self.nav_guide = "\n".join(pages)
        else:
            print("Navigation control PDF not found.")

    def get_files_for_agent(self, agent_type: str):
        """
        Returns a prioritized list of files based on the agent type.
        For example, the LocationAgent prioritizes the 'CONTEXT_Rooms_And_Tasks.pdf'.
        """
        if agent_type == "location":
            prioritized = [f for f in self.files if "CONTEXT_Rooms_And_Tasks.pdf" in f.display_name]
            others = [f for f in self.files if "CONTEXT_Rooms_And_Tasks.pdf" not in f.display_name]
            return prioritized + others
        # For other agent types, return all files.
        return self.files


#########################################
# Base Agent and Specialized Agents
#########################################

class BaseAgent:
    """
    Base class for AI agents. Handles common configuration,
    user name extraction, and query processing.
    """
    def __init__(self, resource_manager: ResourceManager, user_cache: dict, agent_type: str):
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

        # Check for explicit user name in the query
        old_user_name = self.user_cache.get("USER", "User")
        new_user_name = self.extract_user_name(query)
        if new_user_name and new_user_name.lower() != "user" and new_user_name != old_user_name:
            self.user_cache["USER"] = new_user_name
            return (f"Hi! {new_user_name}. Thank you for sharing your name. I will use this for future reference.",
                    {"name_update": 0.0})

        # Ensure resources are loaded
        if not self.resource_manager.loaded:
            raise Exception("Resources not loaded. Please load resources first using ResourceManager.load_resources().")

        # Generate prompt using specialized logic
        prompt = self.generate_prompt(query)
        user_name = self.user_cache.get("USER", "User")
        print(f"Processing query for user: {user_name}")

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
        return response.text, timings


class LocationAgent(BaseAgent):
    def __init__(self, resource_manager: ResourceManager, user_cache: dict):
        super().__init__(resource_manager, user_cache, agent_type="location")

    def generate_prompt(self, query: str) -> str:
        user_name = self.user_cache.get("USER", "User")
        prompt = (
            f"The user who is asking the question is {user_name}. You are a location-aware AI-based chatbot assistant, "
            f"named 'Robi', designed to answer questions and assist users in the VR learning environment. For questions about "
            f"rooms or tasks:\n"
            "1. ONLY use information from 'CONTEXT_Rooms_And_Tasks.pdf'\n"
            "2. Keep response short\n"
            "3. Ignore all other documents completely for room/task questions\n"
            "4. Provide specific task details for the requested room\n"
            "5. If the information isn't in CONTEXT_Rooms_And_Tasks.pdf, say \"I cannot find information about this room/task in the available documents.\"\n"
            "6. Please make sure to provide the best user friendly response using the user's name.\n"
            f"Question: {query}"
        )
        return prompt


class NavigationAgent(BaseAgent):
    def __init__(self, resource_manager: ResourceManager, user_cache: dict):
        super().__init__(resource_manager, user_cache, agent_type="navigation")

    def generate_prompt(self, query: str) -> str:
        user_name = self.user_cache.get("USER", "User")
        # nav_content = self.resource_manager.nav_guide
        return f"""The user who is asking the question is {user_name}. You are a system and navigation aware AI-based chatbot assistant, named 'Robi', designed to answer questions and assist users in the VR learning environment. For navigation and interaction questions:
                            1. ONLY use information from {self.resource_manager.nav_guide}
                            2. Keep Response short
                            3. Ignore all other documents completely for navigation questions
                            4. Provide specific Joystick control for the requested action (like moving forward, turning, etc.)
                            5. If the information isn't in {self.resource_manager.nav_guide}, say "I cannot find information about this navigation/interaction in the available documents."
                            6. Please make sure to provide the best user friendly response using the user's name using only the available resource.
                            
                            Question: {query}"""


class CybersecurityAgent(BaseAgent):
    def __init__(self, resource_manager: ResourceManager, user_cache: dict):
        super().__init__(resource_manager, user_cache, agent_type="cybersecurity")

    def generate_prompt(self, query: str) -> str:
        prompt = (
            "You are 'Robi', an AI-based chatbot assistant, designed as a cybersecurity expert. For security questions:\n"
            "1. Prioritize information from cybersecurity guides and best practices\n"
            "2. Keep it short\n"
            "3. Provide specific, actionable security information\n"
            "4. Only include room or system information if directly relevant to security\n"
            f"Question: {query}"
        )
        return prompt


class SystemAgent(BaseAgent):
    def __init__(self, resource_manager: ResourceManager, user_cache: dict):
        super().__init__(resource_manager, user_cache, agent_type="system")

    def generate_prompt(self, query: str) -> str:
        prompt = (
            "You are 'Robi', an AI-based chatbot assistant, designed as a system configuration assistant. For system questions:\n"
            "1. Focus on technical configuration and asset details\n"
            "2. Keep it short\n"
            "3. Reference room information only if relevant to system setup\n"
            "4. Include security considerations only if directly applicable\n"
            f"Question: {query}"
        )
        return prompt


class GenericAgent(BaseAgent):
    def __init__(self, resource_manager: ResourceManager, user_cache: dict):
        super().__init__(resource_manager, user_cache, agent_type="other")

    def generate_prompt(self, query: str) -> str:
        prompt = (
            "You are 'Robi', an AI-based chatbot assistant, designed to answer questions and assist users in the VR learning environment. "
            "Answer the following question ONLY if the information is found in the provided documents. If the requested information is not available in the resources, respond with:\n"
            "\"I am an AI-based chatbot assistant designed to answer questions about cyber security and your surrounding VR environment. I cannot answer this question based on the available resources.\"\n"
            f"Question: {query}"
        )
        return prompt


#########################################
# Agent Coordinator
#########################################

class AgentCoordinator:
    """
    Routes incoming queries to the appropriate specialized agent.
    """
    def __init__(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager
        self.user_cache = {"USER": "User"}  # Shared user cache across agents
        self.agents = {
            "location": LocationAgent(resource_manager, self.user_cache),
            "navigation": NavigationAgent(resource_manager, self.user_cache),
            "cybersecurity": CybersecurityAgent(resource_manager, self.user_cache),
            "system": SystemAgent(resource_manager, self.user_cache),
            "other": GenericAgent(resource_manager, self.user_cache),
        }

    def detect_query_type(self, query: str) -> str:
        """
        Determines the query type based on a set of keywords.
        """
        query_lower = query.lower()
        location_keywords = ['room', 'location', 'where', 'place', 'area', 'task']
        security_keywords = [
            'security', 'cyber', 'attack', 'threat', 'protection', 'ddos', 'dns',
            'firewall', 'encryption', 'malware', 'phishing', 'ransomware',
            'vulnerability', 'penetration', 'breach', 'authentication', 'intrusion',
            'zero-day', 'exploit', 'mitigation', 'defense', 'incident', 'forensics',
            'safety', 'network security', 'data breach', 'password', 'access control',
            'ids', 'ips', 'iot security', 'cloud security', 'endpoint security',
            'web security', 'mobile security'
        ]
        system_keywords = [
            'controller', 'system', 'asset', 'configuration', 'architecture',
            'setup', 'installation', 'framework', 'protocol', 'integration',
            'hardware', 'software', 'deployment', 'infrastructure', 'operating system',
            'network', 'server', 'database', 'automation', 'monitoring',
            'maintenance', 'device', 'tool', 'resource management', 'scalability'
        ]
        navigation_keywords = [
            'move', 'go', 'navigate', 'walk', 'forward', 'backward', 'strafe',
            'left', 'right', 'joystick', 'speed', 'pace', 'rotate', 'turn',
            'perspective', 'direction', 'adjust', 'push', 'pressure', 'click',
            'button', 'trigger', 'grip', 'a button', 'b button',
            'interact', 'grab', 'hold', 'drop', 'summon', 'robi',
            'object', 'icon', 'box', 'select', 'outline', 'highlight',
            'hover', 'conversation', 'appear', 'materialize', 'hear',
            'respond', 'audio input', 'release', 'troubleshoot'
        ]

        if any(keyword in query_lower for keyword in location_keywords):
            return "location"
        elif any(keyword in query_lower for keyword in security_keywords):
            return "cybersecurity"
        elif any(keyword in query_lower for keyword in system_keywords):
            return "system"
        elif any(keyword in query_lower for keyword in navigation_keywords):
            return "navigation"
        return "other"

    def route_query(self, query: str):
        """
        Routes the query to the appropriate agent based on its type.
        """
        query_type = self.detect_query_type(query)
        agent = self.agents.get(query_type, self.agents["other"])
        answer, timings = agent.get_answer(query)
        return answer, timings