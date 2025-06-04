from typing import List, Optional, Dict
from pydantic import BaseModel


class CodeAgent:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.conversation_history: List[Dict[str, str]] = []
        
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.conversation_history.append({"role": role, "content": content})
        
    def process_message(self, message: str) -> str:
        """
        Process a user message and return a response.
        
        Args:
            message: The user's message
            context: Optional list of context strings
            
        Returns:
            tuple: (response message, list of tool calls)
        """
        # Add user message to history
        self.add_message("user", message)
        
        # TODO: Implement actual LLM processing
        # For now, just echo back
        response = f"Echo: {message}"
        self.add_message("assistant", response)
        
        return response