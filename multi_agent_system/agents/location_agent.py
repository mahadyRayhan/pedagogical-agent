import re
from .base_agent import BaseAgent

class LocationAgent(BaseAgent):
    def __init__(self, resource_manager, user_cache: dict):
        super().__init__(resource_manager, user_cache, agent_type="location")
        
    def extract_room_name(self, query: str) -> str:
        """
        Extracts a room name from the query if present.
        Example: "where am i, roomname: room3" returns "room3".
        """
        # room_pattern = r"roomname:\s*(\w+)"
        room_pattern = r"(?:roomname|room name|current room):?\s*(\w+)"
        match = re.search(room_pattern, query, re.IGNORECASE)
        if match:
            return match.group(1)
        return None
    
    def extract_room_name_API(self, query: str) -> str:
        """
        Extracts a room name from the query using an API call.
        Example: "where am i, roomname: room3" returns "room3".
        """
        extraction_prompt = (
            f"Extract the room name from the following query and only return the room name without any additional text:\n\n"
            f"Query: {query}\n\n"
            f"Room name:"
        )
        # Call the generative API to extract the room name.
        response = self.chat_session.send_message(extraction_prompt, safety_settings=self.safety_settings)
        extracted_room = response.text.strip()
        
        # Optionally add post-processing if needed.
        if extracted_room:
            return extracted_room
        else:
            return None

    def get_answer(self, query: str):
        """
        If the query contains 'where am I', extract and return the room name directly.
        Otherwise, proceed with the default behavior.
        """
        # Check if the query contains "where am I" (case-insensitive)
        if "where am i" in query.lower():
            room_name = self.extract_room_name(query)
            if room_name:
                return f"Your room is {room_name}.", {"extracted": True}
            else:
                return "I could not extract a room name from your query.", {"extracted": True}
        
        # Otherwise, continue with the default processing
        return super().get_answer(query)

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
