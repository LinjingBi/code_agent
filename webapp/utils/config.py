import os
from typing import Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
import yaml
from jinja2 import Environment, FileSystemLoader
from tool.tool import tool_registry

# Load environment variables from .env file
load_dotenv()



def load_prompt_from_yaml(cls, yaml_path: str = "prompt.yaml") -> 'Settings':
    """Load settings from YAML file."""
    try:
        env = Environment(loader=FileSystemLoader('utils'))
        template = env.get_template(yaml_path)
        
        config_data = yaml.safe_load(template.render(tools=tool_registry.get_tools()))

        api_key = os.getenv("API_KEY")
        model_name = os.getenv("MODEL_NAME", "gpt-3.5-turbo")
        
        return cls(
            system_prompt=config_data.get("system_prompt", ""),
            api_key=api_key,
            model_name=model_name
        )
    except Exception as e:
        raise Exception(f"Error loading config from {yaml_path}: {str(e)}")

# settings = Settings.load_from_yaml()
