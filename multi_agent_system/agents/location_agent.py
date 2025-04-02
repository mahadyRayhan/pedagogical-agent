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

    # def get_answer(self, query: str):
    #     """
    #     If the query contains 'where am I', extract and return the room name directly.
    #     Otherwise, proceed with the default behavior.
    #     """
    #     # Check if the query contains "where am I" (case-insensitive)
    #     if "where am i" in query.lower():
    #         room_name = self.extract_room_name(query)
    #         if room_name:
    #             return f"Your room is {room_name}.", {"extracted": True}
    #         else:
    #             return "I could not extract a room name from your query.", {"extracted": True}
        
    #     # Otherwise, continue with the default processing
    #     return super().get_answer(query)
    
    # def get_answer(self, query: str):

    #     room_name = self.extract_room_name(query)
    #     user_name = self.user_cache.get("USER", "User")
    #     print("Location Agent: Extracted user name:", user_name)

    #     # Split the query by "?" and remove empty parts
    #     parts = [part.strip() for part in query.split('?') if part.strip()]

    #     # If exactly two parts and the first part is "where am i", return a simple answer.
    #     if len(parts) == 2 and parts[0].lower() == "where am i":
    #         if room_name:
    #             return f"Hello {user_name}! You are in {room_name}.", {"extracted": True}
    #         else:
    #             return f"Hello {user_name}! I could not extract your room.", {"extracted": True}
    #     else:
    #         # Otherwise, proceed with the full processing:
    #         # Optionally, include room info in the query to the superclass.
    #         query_to_send = f"{query}" if room_name else query
    #         print("Location Agent: Query to send to super:", query_to_send)
    #         super_response, super_metadata = super().get_answer(query_to_send)
            
    #         # Prepare a room message for the final response.
    #         if room_name:
    #             room_message = f"Your room is {room_name}."
    #         else:
    #             room_message = "I could not extract your room."
            
    #         # Remove any duplicate greetings (e.g., "Hello", "Hello User!") from the super response
    #         cleaned_super_response = re.sub(r"(?i)^hello\s+(user[!,:]?\s+)?", "", super_response).strip()

    #         # Format the final answer with a single greeting
    #         final_response = f"Hello {user_name}! {room_message} {cleaned_super_response}".strip()
    #         final_response = re.sub(r'\s+', ' ', final_response)  # Normalize whitespace
            
    #         print("Location Agent: room_message:", room_message)
    #         print("Location Agent: super_response:", super_response)

    #         # Return the combined answer along with metadata
    #         combined_metadata = {"extracted": True}
    #         combined_metadata.update(super_metadata)
            
    #         return final_response, combined_metadata


    def generate_prompt(self, query: str) -> str:
        user_name = self.user_cache.get("USER", "User")
        # prompt = (
        #     f"The user who is asking the question is {user_name}. You are a location-aware AI-based chatbot assistant, "
        #     f"named 'Robi', designed to answer questions and assist users in the VR learning environment. For questions about "
        #     f"rooms or tasks:\n"
        #     "1. ONLY use information from 'CONTEXT_Rooms_And_Tasks.pdf'\n"
        #     "2. Keep response short\n"
        #     "3. Ignore all other documents completely for room/task questions\n"
        #     "4. Provide specific task details for the requested room\n"
        #     "5. If the information isn't in CONTEXT_Rooms_And_Tasks.pdf, say \"I cannot find information about this room/task in the available documents.\"\n"
        #     "6. Please make sure to provide the best user friendly response using the user's name.\n"
        #     f"Question: {query}"
        # )
        
        prompt = (
            f"The user asking the question is {user_name}. You are Robi, a location-aware AI chatbot assistant, here to help guide users in their VR learning environment. When answering questions about rooms or tasks, please follow these friendly guidelines:"
            "1. ONLY use information from 'CONTEXT_Rooms_And_Tasks.pdf'."
            "2. Keep your response short and to the point."
            "3. Ignore any other documents when addressing room/task questions."
            "4. Provide clear, specific task details for the requested room."
            "5. If the information isn't in 'CONTEXT_Rooms_And_Tasks.pdf', kindly say, \"I'm sorry, but I don't have enough information to answer that question right now. I focus on information about room and or task inside VR environment, so feel free to ask about those topics and I'll be happy to help!\""
            "6. Make sure to address the user by name for a personalized response."
            f"Question: {query}"
        )
        return prompt
