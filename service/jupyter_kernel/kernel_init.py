from tools import final_answer, search, tool

# Make tools available in the kernel's global namespace
__builtins__['final_answer'] = final_answer
__builtins__['search'] = search

# Print available tools
print("Available tools:")
for tool_name, tool_info in tool.get_tools().items():
    print(f"- {tool_name}: {tool_info['description']}") 