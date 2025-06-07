from typing import List, Dict

def format_chat_history(messages: List[Dict[str, str]]) -> str:
    """Format chat history for console output.
    
    Args:
        messages: List of message dictionaries with 'role' and 'content' keys
        
    Returns:
        Formatted chat history string
    """
    output = []
    output.append("\n" + "="*80)
    output.append("CHAT HISTORY")
    output.append("="*80)
    
    for msg in messages:
        role = msg["role"].upper()
        content = msg["content"]
        
        # Print role header
        output.append(f"\n[{role}]")
        output.append("-" * (len(role) + 2))
        
        # Print content with proper indentation
        if "Thought:" in content and "Code:" in content:
            # Split thought and code sections
            thought, code = content.split("Code:", 1)
            thought = thought.replace("Thought:", "").strip()
            code = code.strip()
            
            # Print thought
            output.append("Thought:")
            for line in thought.split('\n'):
                output.append(f"  {line}")
            
            # Print code
            output.append("\nCode:")
            for line in code.split('\n'):
                output.append(f"  {line}")
        else:
            # Regular message
            for line in content.split('\n'):
                output.append(f"  {line}")
        
        output.append("-"*80)
    
    return "\n".join(output) 