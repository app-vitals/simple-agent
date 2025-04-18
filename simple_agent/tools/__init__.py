"""Tool registry for Simple Agent."""

from typing import Any

# Import tool functions
from simple_agent.tools.exec import execute_command
from simple_agent.tools.files import patch_file, read_files, write_file

# Tool definitions with metadata
TOOLS: dict[str, dict[str, Any]] = {
    "read_files": {
        "function": read_files,
        "description": "Read the contents of one or more files in a single operation for improved efficiency",
        "parameters": {
            "file_paths": {
                "type": "array",
                "description": "List of file paths to read (for efficiency, include multiple files when needed)",
                "items": {"type": "string"},
            }
        },
        "returns": "Dictionary mapping each file path to its content or None if an error occurred",
        "requires_confirmation": False,  # Reading files doesn't modify the system
    },
    "write_file": {
        "function": write_file,
        "description": "Write content to a file",
        "parameters": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to write",
            },
            "content": {
                "type": "string",
                "description": "Content to write to the file",
            },
        },
        "returns": "True if successful, False otherwise",
        "requires_confirmation": True,  # Modifies the system
    },
    "patch_file": {
        "function": patch_file,
        "description": "Replace specific content in a file",
        "parameters": {
            "file_path": {
                "type": "string",
                "description": "Path to the file to patch",
            },
            "old_content": {
                "type": "string",
                "description": "Content to be replaced",
            },
            "new_content": {
                "type": "string",
                "description": "New content to replace with",
            },
        },
        "returns": "True if successful, False otherwise",
        "requires_confirmation": True,  # Modifies the system
    },
    "execute_command": {
        "function": execute_command,
        "description": "Execute a shell command",
        "parameters": {
            "command": {
                "type": "string",
                "description": "Command to execute",
            }
        },
        "returns": "Tuple containing (stdout, stderr, return_code)",
        "requires_confirmation": True,  # Modifies the system
    },
}


def get_tool_descriptions() -> list[dict[str, Any]]:
    """Get descriptions of available tools in a format suitable for LLM tool calling.

    Returns:
        List of tool descriptions compatible with LLM tool calling format
    """
    tool_descriptions = []
    for tool_name, tool_info in TOOLS.items():
        tool_descriptions.append(
            {
                "type": "function",
                "function": {
                    "name": tool_name,
                    "description": tool_info["description"],
                    "parameters": {
                        "type": "object",
                        "properties": {
                            param_name: {
                                "type": param_info["type"],
                                "description": param_info["description"],
                            }
                            for param_name, param_info in tool_info[
                                "parameters"
                            ].items()
                        },
                        "required": list(tool_info["parameters"].keys()),
                    },
                },
            }
        )
    return tool_descriptions


def requires_confirmation(tool_name: str) -> bool:
    """Check if a tool requires user confirmation before execution.

    Args:
        tool_name: Name of the tool

    Returns:
        True if the tool requires confirmation, False otherwise
    """
    if tool_name not in TOOLS:
        return True  # Default to requiring confirmation for unknown tools

    requires_confirm = TOOLS[tool_name].get("requires_confirmation", True)
    return bool(requires_confirm)  # Ensure we return a bool


def execute_tool_call(tool_name: str, arguments: dict[str, Any]) -> Any:
    """Execute a specific tool with the provided arguments.

    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments to pass to the tool

    Returns:
        Result of the tool execution, or an error message
    """
    if tool_name not in TOOLS:
        return f"Error: Tool '{tool_name}' not found"

    tool_function = TOOLS[tool_name]["function"]

    try:
        # Execute the tool with the provided arguments
        return tool_function(**arguments)
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"
