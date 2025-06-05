from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator
from llm.openrouter import OpenRouter
from utils.logging import setup_logger
from utils.chat_formatter import format_chat_history
import os

# Set up logger
logger = setup_logger(__name__)

class CodeAgentResponse(BaseModel):
    """Response model for code agent that enforces thought/code format."""
    thought: str = Field(..., description="The agent's reasoning about what to do")
    code: str = Field(..., description="The code to execute")

    @field_validator('thought', 'code')
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

class CodeAgent:
    def __init__(self, system_prompt):
        self.system_prompt = system_prompt
        self.messages: List[Dict[str, str]] = []
        self.llm = OpenRouter(api_key=os.getenv("API_KEY"))
        self.add_message('system', self.system_prompt)
        
    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})
    
    async def process_message(self, message: str) -> CodeAgentResponse:
        """Process a user message and return the agent's response.
        
        Args:
            message: The user's message
            
        Returns:
            CodeAgentResponse containing thought and code
            
        Raises:
            ValueError: If the response format is invalid
        """
        # Add user message to history
        self.add_message("user", message)
        logger.info("User message added to history")
        
        try:
            # Get completion from OpenRouter
            response = await self.llm.chat_completion(
                messages=self.messages,
                model="deepseek/deepseek-r1-0528-qwen3-8b:free",
                temperature=0.7,
                top_p=0.95,
            )
            logger.info("Received response from LLM")
            
            # Parse and validate response
            try:
                import json
                response_dict = json.loads(response)
                agent_response = CodeAgentResponse(**response_dict)
            except json.JSONDecodeError:
                # Try to extract thought and code from text
                thought_start = response.find("Thought:")
                code_start = response.find("Code:")
                
                if thought_start == -1 or code_start == -1:
                    raise ValueError("Response must contain 'Thought:' and 'Code:' sections")
                
                thought = response[thought_start + 8:code_start].strip()
                code = response[code_start + 5:].strip()
                
                agent_response = CodeAgentResponse(thought=thought, code=code)
            
            # Add assistant's response to history
            self.add_message("assistant", f"Thought: {agent_response.thought}\nCode: {agent_response.code}")
            logger.info("Assistant response added to history")
            logger.info(format_chat_history(self.messages))
            
            return agent_response
            
        except Exception as e:
            error_msg = f"Error processing message: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.add_message("assistant", f"Error: {error_msg}")
            raise ValueError(error_msg)
    
    async def close(self):
        """Close the LLM client."""
        await self.llm.close() 