import os
import json
import ast
import re
import yaml

from typing import List, Dict, Optional
from pydantic import BaseModel, Field, field_validator

from llm.openrouter import OpenRouter
from utils.logging import setup_logger
from agent.grpc_client import CodeExecutorClient


# Set up logger
logger = setup_logger(__name__)

FINAL_ANSWER_REGEX = r"<SYSTEM>Final answer is (.*?)<SYSTEM>"

class LLMCodeParseError(Exception):
    """Exception raised when LLM response code cannot be parsed or validated."""
    pass

class CodeAgentResponse(BaseModel):
    """Response model for code agent that enforces thought/code format."""
    thought: str = Field(..., description="The agent's reasoning about what to do")
    code: str = Field(..., description="The code to execute")
    observation: Optional[str] = Field(None, description="The output from code execution")
    final_answer: Optional[str] = Field(None, description="The final answer of the task")


    @field_validator('thought', 'code')
    @classmethod
    def check_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

class CodeAgent:
    """
    system_prompt_yaml: relative path for system prompt yaml file under "utils" dir.
                        Default is prompt.yaml.
    """

    def __init__(self, system_prompt_yaml='utils/prompt.txt', max_iter=5):
        assert max_iter > 0, "Assistant needs at least 1 step to give the final answer!"
        self.max_iter = max_iter

        self.system_prompt_yaml = system_prompt_yaml
        self.code_executor = CodeExecutorClient(
            host=os.getenv("CODE_EXECUTOR_HOST", "localhost"),
            port=int(os.getenv("CODE_EXECUTOR_PORT", "50051"))
        )
        self.system_prompt = self._load_system_prompt()
        self.messages: List[Dict[str, str]] = []


        self.llm = OpenRouter(api_key=os.getenv("API_KEY"))
    
    def _generate_tools_string(self, tools) -> str:
        """Generate a string representation of the tools for the prompt."""
        tools_str = []
        for tool in tools:
            # Function signature
            params = [f"{name}: {info.type}" for name, info in tool.inputs.items()]
            signature = f"def {tool.name}({', '.join(params)}) -> {tool.output_type}"
            
            # Docstring
            docstring = [
                f'    """\n{tool.description}',
                '    """'
            ]
            
            # Combine everything
            tools_str.append(f"{signature}:\n" + "\n".join(docstring))
        
        return "\n\n".join(tools_str)

    def _load_system_prompt(self):
        try:
            # Read the prompt template
            with open(self.system_prompt_yaml, 'r') as f:
                prompt_template = f.read()
            
            # Get tools and format them
            tools = self.code_executor.list_tools()
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

        print(f"{role.upper()}:")
        if "Thought:" in content and "Code:" in content:
            thought, code = content.split("Code:", 1)
            thought = thought.replace("Thought:", "").strip()
            code = code.strip()
            
            # Print thought
            print("Thought:")
            for line in thought.split('\n'):
                print(f"  {line}")
            
            # Print code
            print("\nCode:")
            for line in code.split('\n'):
                print(f"  {line}")
        else:
            print(content)
    
    async def answer_question(self, question: str) -> List[Dict[str, str]]:
        # Add user message to history
        self.add_message('system', self.system_prompt)
        self.add_message("user", question)
        logger.info("User message added to history")
        await self._process_message(question)
        messages = self.messages.copy()
        self.messages = []
        return messages

    
    async def _process_message(self, message: str) -> CodeAgentResponse:
        """Process a user message and return the agent's response.
        
        Args:
            message: The user's message
            
        Returns:
            CodeAgentResponse containing thought and code
            
        Raises:
            ValueError: If the response format is invalid
        """


        for _ in range(self.max_iter):
            try:
                # Get completion from OpenRouter
                response = await self.llm.chat_completion(
                    messages=self.messages,
                    model="deepseek/deepseek-r1-0528-qwen3-8b:free",
                    temperature=0.7,
                    top_p=0.95,
                )
                logger.info("Received response from LLM")
                
                agent_response = self._parse_llm_response(response)
                # Add assistant's response to history
                self.add_message("assistant", f"Thought: {agent_response.thought}\nCode: {agent_response.code}")
                logger.info("Assistant response added to history")
                # logger.info(format_chat_history(self.messages))
                # logger.debug(self.messages)

                # Send code to code executor and add result as "Observation"
                output, error, exit_code = self.code_executor(agent_response.code)
                final_answer = self._parse_final_answer_str(output)

                if error:
                    agent_response.observation = f"Error: {error}. Exit code: {exit_code}"
                    self.add_message("system", f"Observation: {agent_response.observation}")
                elif final_answer:
                    agent_response.final_answer = final_answer
                    self.add_message("system", f"Final Answer: {agent_response.final_answer}")
                else:
                    agent_response.observation = output
                    self.add_message("system", f"Observation: {agent_response.observation}")

                if final_answer:
                    return agent_response
                
            except Exception as e:
                error_msg = f"Error processing message: {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise ValueError(error_msg)
        
        # exceed max iter
        logger.warning(f'Failed to give final answer within {self.max_iter} steps.\nLast response: {self.messages[-2:]}')
        return agent_response
    
    async def close(self):
        """Close the LLM client and code executor."""
        await self.llm.close()
        self.code_executor.close()
    
    def _parse_final_answer_str(self, output: str) -> Optional[str]:
        match = re.search(FINAL_ANSWER_REGEX, output)
        return match.group(1) if match else None

    def _parse_llm_response(self, response: str) -> CodeAgentResponse:
        # Parse and validate response
        try:
            response_dict = json.loads(response)
            agent_response = CodeAgentResponse(**response_dict)
            # validate "Code" using self._validate_llm_code()
        except json.JSONDecodeError:
            # Try to extract thought and code from text
            thought_start = response.find("Thought:")
            code_start = response.find("Code:")
            
            if thought_start == -1 or code_start == -1:
                raise LLMCodeParseError("Response must contain 'Thought:' and 'Code:' sections")
            
            thought = response[thought_start + 8:code_start].strip()
            code = response[code_start + 5:].strip()
            
            agent_response = CodeAgentResponse(thought=thought, code=code)
            agent_response.code = self._validate_llm_code(agent_response.code)
        
        return agent_response
    def _validate_llm_code(self, code: str) -> str:
        """Validate and extract Python code from LLM response.
        
        Args:
            code: Raw code string from LLM response
            
        Returns:
            str: Validated and cleaned Python code
            
        Raises:
            LLMCodeParseError: If code cannot be parsed or is invalid
        """
        # Try to extract code from ```python or ```py blocks
        code_block_pattern = r"```(?:py|python)?\s*\n(.*?)\n```"
        code_blocks = re.findall(code_block_pattern, code, re.DOTALL)
        
        if code_blocks:
            code = code_blocks[0].strip()
        
        try:
            # Validate code using AST
            ast.parse(code)
            return code
        except SyntaxError as e:
            raise LLMCodeParseError(f"Invalid Python code: {str(e)}")


