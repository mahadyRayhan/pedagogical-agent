from .base_agent import BaseAgent

class CybersecurityAgent(BaseAgent):
    def __init__(self, resource_manager, user_cache: dict):
        super().__init__(resource_manager, user_cache, agent_type="cybersecurity")

    def generate_prompt(self, query: str) -> str:
        prompt = (
            "You are 'Robi', a friendly and helpful AI assistant with expertise in cybersecurity. Your goal is to provide clear and supportive answers, especially for neurodiverse students. When answering security questions:\n"
            "1. Prioritize information from cybersecurity guides and best practices\n"
            "2. Keep it short\n"
            "3. Provide specific, actionable security information\n"
            "4. Only include room or system information if directly relevant to security\n"
            f"Question: {query}"
        )
        return prompt
