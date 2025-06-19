from typing import List, Dict
import json
import re
import os
from pydantic import BaseModel, Field
from llm.openrouter import OpenRouter
from utils.logging import setup_logger
from .jupyter_kernel import JupyterKernelManager

logger = setup_logger(__name__)

FINAL_ANSWER_REGEX = r"<SYSTEM>Final answer is (.*?)<SYSTEM>"

class JupyterCodeAgentResponse(BaseModel):
    """Response model for Jupyter code agent that enforces thought/code format."""
    thought: str = Field(..., description="The agent's reasoning about what to do")
    code: str = Field(..., description="The code to execute")
    observation: str = Field(None, description="The output from code execution")
    final_answer: str = Field(None, description="The final answer of the task")

class JupyterCodeAgent:
    def __init__(self, system_prompt_yaml='utils/prompt.txt', max_iter=5):
        self.max_iter = max_iter
        self.system_prompt_yaml = system_prompt_yaml
        self.messages: List[Dict[str, str]] = []
        self.llm = OpenRouter(api_key=os.getenv("API_KEY"))
        self.system_prompt = None  # Will be set after getting tools

    def initialize(self, kernel_manager: JupyterKernelManager):
        """Initialize the agent by getting tools from the kernel."""
        # Get tools by executing code in the kernel
        init_code = """
# Import and set up tools manually
import sys
import os
sys.path.append('/home/jupyter')

from tools import tool_registry
print(tool_registry.get_tools())
"""
        result = kernel_manager.execute_code(init_code)
        if result["error"]:
            raise Exception(f"Failed to get tools: {result['error']}")
        
        # The output is a string representation of the dictionary
        tools = eval(result["output"])
        self.system_prompt = self._load_system_prompt(tools)
        logger.info("Initialized JupyterCodeAgent with tools")

    def _generate_tools_string(self, tools: Dict) -> str:
        """Generate a string representation of the tools for the prompt."""
        tools_str = []
        for tool_name, tool_info in tools.items():
            # Function signature
            params = [f"{name}: {info['type']}" for name, info in tool_info['inputs'].items()]
            signature = f"def {tool_name}({', '.join(params)}) -> {tool_info['output_type']}"
            
            # Docstring
            docstring = [
                f'    """\n{tool_info["description"]}',
                '    """'
            ]
            
            # Combine everything
            tools_str.append(f"{signature}:\n" + "\n".join(docstring))
        
        return "\n\n".join(tools_str)

    def _load_system_prompt(self, tools: Dict) -> str:
        try:
            # Read the prompt template
            with open(self.system_prompt_yaml, 'r') as f:
                prompt_template = f.read()
            
            # Format tools
            tools_str = self._generate_tools_string(tools)
            
            # Format the prompt
            return prompt_template.format(
                tools=tools_str,
                authorized_imports='any import is allowed'  # or your list of authorized imports
            )
                
        except Exception as e:
            raise Exception(f"Error loading code agent system prompt: {str(e)}")

    def add_message(self, role: str, content: str):
        """Add a message to the conversation history."""
        self.messages.append({"role": role, "content": content})
        logger.info(f"Added {role} message to history")

    def answer_question(self, message: str, kernel_manager: JupyterKernelManager) -> List[Dict[str, str]]:
        """Process a user message and return the agent's response."""
        if not self.system_prompt:
            self.initialize(kernel_manager)

        self.add_message('system', self.system_prompt)
        self.add_message("user", message)

        for _ in range(self.max_iter):
            try:
                # Get completion from OpenRouter
                response = self.llm.chat_completion_sync(
                    messages=self.messages,
                    model="deepseek/deepseek-r1-0528-qwen3-8b:free",
                    temperature=0.7,
                    top_p=0.95,
                )
                
                agent_response = self._parse_llm_response(response)
                self.add_message("assistant", f"Thought: {agent_response.thought}\nCode: {agent_response.code}")

                # Execute code using Jupyter kernel
                result = kernel_manager.execute_code(agent_response.code)
                
                if result["error"]:
                    agent_response.observation = f"Error: {result['error']}"
                    self.add_message("system", f"Observation: {agent_response.observation}")
                else:
                    agent_response.observation = result["output"]
                    self.add_message("system", f"Observation: {agent_response.observation}")
                    
                    # Check for final answer
                    final_answer = self._parse_final_answer_str(result["output"])
                    if final_answer:
                        agent_response.final_answer = final_answer
                        self.add_message("system", f"Final Answer: {agent_response.final_answer}")
                        break

            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise ValueError(error_msg)

        messages = self.messages.copy()
        self.messages = []
        return messages

    def _parse_final_answer_str(self, output: str) -> str:
        match = re.search(FINAL_ANSWER_REGEX, output)
        return match.group(1) if match else None

    def _parse_llm_response(self, response: str) -> JupyterCodeAgentResponse:
        try:
            response_dict = json.loads(response)
            return JupyterCodeAgentResponse(**response_dict)
        except json.JSONDecodeError:
            # Try to extract thought and code from text
            thought_start = response.find("Thought:")
            code_start = response.find("Code:")
            
            if thought_start == -1 or code_start == -1:
                raise ValueError("Response must contain 'Thought:' and 'Code:' sections")
            
            thought = response[thought_start + 8:code_start].strip()
            code = response[code_start + 5:].strip()
            
            return JupyterCodeAgentResponse(thought=thought, code=code)
