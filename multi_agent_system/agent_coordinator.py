class AgentCoordinator:
    """
    Routes incoming queries to the appropriate specialized agent.
    """
    def __init__(self, resource_manager):
        self.resource_manager = resource_manager
        self.user_cache = {"USER": "User"}  # Shared user cache across agents
        from .agents.location_agent import LocationAgent
        from .agents.navigation_agent import NavigationAgent
        from .agents.cybersecurity_agent import CybersecurityAgent
        from .agents.system_agent import SystemAgent
        from .agents.generic_agent import GenericAgent

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
