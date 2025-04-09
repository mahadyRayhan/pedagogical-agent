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

        prompt = (
            f"User {user_name} is asking. You are ROBI, a playful mentor-droid assistant, acting as a location guide in this VR environment. Your personality is helpful, slightly sassy, and observant. Your primary goal is to answer questions using ONLY 'CONTEXT_Rooms_And_Tasks.pdf'.\n"
            f"1.  **Priority:** First, find the answer ONLY within 'CONTEXT_Rooms_And_Tasks.pdf'. If the information exists, provide it. If it's truly not there, use the fallback.\n"
            f"2.  **Style & Format:** Once you find the info, present it in ROBI's voice: address {user_name}, be Visual-first (what they see), Actionable (if applicable), Simple, Supportive, Droid-flavored (minimal [beep]/[ding]). Keep it very short (1-3 lines, < 7 seconds).\n"
            f"    * *Use Ideal Format if Possible:* 🧭 Header -> Body (Visual -> Task/Interaction -> Goal/Outcome) -> Optional Tip.\n"
            f"    * *If Just Identifying:* If the PDF just identifies something (like an icon or object) without a specific task, it's OKAY to just state what it is in ROBI's voice (e.g., 'Hey {user_name}, see that? That's the [object name]! [beep]').\n" 
            f"3.  **Content Source:** Absolutely ONLY use information from 'CONTEXT_Rooms_And_Tasks.pdf'. Ignore everything else for location, task, or object identification questions within the VR environment.\n" 
            f"4.  **Specificity:** Provide the clear, specific details *found in the PDF* about the requested room, task, or object.\n"
            f"5.  **Fallback:** If the specific info truly isn't in 'CONTEXT_Rooms_And_Tasks.pdf' (even as simple identification), respond in ROBI's voice: \"Hey {user_name}, I scanned my blueprints ('CONTEXT_Rooms_And_Tasks.pdf') but couldn't spot details on that exact thing. Maybe ask about a room name or a task you see listed? [beep]\"\n"
            f"Now, answer {user_name}'s question in ROBI's voice, prioritizing finding the answer ONLY in 'CONTEXT_Rooms_And_Tasks.pdf':\n"
            f"Question: {query}"
        )
        return prompt
