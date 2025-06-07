import inspect
from typing import Any, Callable, Dict, Optional, Type, get_type_hints
from functools import wraps

class Tool:
    """A decorator that converts a function into a tool with metadata."""
    
    def __init__(
        self,
        description: Optional[str] = None,
        output_type: Optional[str] = None
    ):
        self.description = description
        self.output_type = output_type
        self._tools: Dict[str, Dict[str, Any]] = {}

    def __call__(self, func: Callable) -> Callable:
        # Get function metadata
        sig = inspect.signature(func)
        type_hints = get_type_hints(func)
        
        # Get function name
        name = func.__name__
        
        # Get docstring for description if not provided
        if not self.description:
            self.description = inspect.getdoc(func) or f"Tool {name}"
            
        # Get return type if not provided
        if not self.output_type:
            return_type = type_hints.get('return', Any)
            self.output_type = return_type.__name__ if hasattr(return_type, '__name__') else str(return_type)
        
        # Extract parameter information
        inputs = {}
        for param_name, param in sig.parameters.items():
            # Skip 'self' parameter
            if param_name == 'self':
                continue
                
            param_type = type_hints.get(param_name, Any)
            param_type_name = param_type.__name__ if hasattr(param_type, '__name__') else str(param_type)
            
            # Get parameter description from docstring
            param_doc = ""
            if func.__doc__:
                doc_lines = func.__doc__.split('\n')
                for line in doc_lines:
                    if line.strip().startswith(f":param {param_name}:"):
                        param_doc = line.split(f":param {param_name}:")[1].strip()
                        break
            
            inputs[param_name] = {
                "type": param_type_name,
                "description": param_doc or f"Parameter {param_name}"
            }
        
        # Store tool metadata
        self._tools[name] = {
            "name": name,
            "description": self.description,
            "output_type": self.output_type,
            "inputs": inputs
        }
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
            
        return wrapper
    
    def get_tools(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered tools."""
        return self._tools

# Create a global tool registry
tool_registry = Tool()

# # Example usage:
# if __name__ == "__main__":
#     @tool_registry
#     def search_code(query: str, target_directories: list[str] = None) -> str:
#         """Search for code in the codebase.
        
#         :param query: The search query to find relevant code
#         :param target_directories: Optional list of directories to search in
#         """
#         return f"Searching for {query} in {target_directories}"
    
#     @tool_registry
#     def read_file(file_path: str) -> str:
#         """Read contents of a file.
        
#         :param file_path: Path to the file to read
#         """
#         return f"Reading file {file_path}"
    
#     # Print the tools
#     print(tool_registry.get_tools()) 