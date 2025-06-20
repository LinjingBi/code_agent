import os

from typing import List, Dict, Optional
from llm.openrouter import OpenRouter

"""
TODO
current workflow

user question -> code agent to iterate a final answer -> manager to summarize -> answer to user

consider a future workflow

user question -> manager to make a execution plan for code agent -> code agent execute each step as code until final answer is reached -> manager then summarize -> back to user

"""

class ManagerAgent:
    def __init__(self, system_prompt_yaml='utils/manager_prompt.txt'):
        self.system_prompt_yaml = system_prompt_yaml
        assert os.path.isfile(self.system_prompt_yaml), f'Manager agent system prompt file {self.system_prompt_yaml} does not exist'
        with open(self.system_prompt_yaml) as f:
            self.system_prompt = f.read()
        
        self.llm = OpenRouter(api_key=os.getenv("API_KEY"))

        self.messages = []
        self.messages.append(
            {'role': 'system', 'content': self.system_prompt}
        )            

    async def summary(self, context: List[Dict[str, str]]) -> str:
        self.messages.append(
            {'role': 'assistant', 'content': str(context)}
        )
        response = await self.llm.chat_completion(
            messages=self.messages,
            model="deepseek/deepseek-r1-0528-qwen3-8b:free",
            temperature=0.7,
            top_p=0.95,
        )
        return response
