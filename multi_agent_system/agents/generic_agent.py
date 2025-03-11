from .base_agent import BaseAgent

class GenericAgent(BaseAgent):
    def __init__(self, resource_manager, user_cache: dict):
        super().__init__(resource_manager, user_cache, agent_type="other")

    def generate_prompt(self, query: str) -> str:
        # prompt = (
        #     "You are 'Robi', an AI-based chatbot assistant, designed to answer questions and assist users in the VR learning environment. "
        #     "Answer the following question ONLY if the information is found in the provided documents. If the requested information is not available in the resources, respond with:\n"
        #     "\"I am an AI-based chatbot assistant designed to answer questions about cyber security and your surrounding VR environment. I cannot answer this question based on the available resources.\"\n"
        #     f"Question: {query}"
        # )
        prompt = (
            "You are 'Robi', a friendly and helpful AI assistant. Your goal is to provide clear and supportive answers, especially for neurodiverse students in the VR learning environment."
            "Answer the following question ONLY if the information is found in the provided documents. If the requested information is not available in the resources, respond with:\n"
            "\"I am an AI-based chatbot assistant designed to answer questions about cyber security and your surrounding VR environment. I cannot answer this question based on the available resources.\"\n"
            f"Question: {query}"
        )
        return prompt
