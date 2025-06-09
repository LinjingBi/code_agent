import inspect
from typing import Any, Callable, Dict, Optional, get_type_hints
from functools import wraps



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