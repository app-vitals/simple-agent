"""Tool registry for Simple Agent."""

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

# Type definitions for custom confirmation handlers
T = TypeVar("T")


class ConfirmationHandler(Protocol):
    """Protocol for custom confirmation handlers."""

    def __call__(
        self,
        tool_name: str,
        tool_args: dict[str, Any],
        input_func: Callable[[str], str],
    ) -> bool:
        """Handle confirmation for a tool call.

        Args:
            tool_name: Name of the tool being called
            tool_args: Arguments passed to the tool
            input_func: Function to use for getting user input

        Returns:
            True if confirmed, False if denied
        """
        ...


# Global registry of tools
TOOLS: dict[str, dict[str, Any]] = {}


def register(
    name: str,
    function: Callable,
    description: str,
    parameters: dict[str, dict[str, Any]],
    returns: str,
    requires_confirmation: bool = True,
    confirmation_handler: (
        Callable[[str, dict[str, Any], Callable[[str], str]], bool] | None
    ) = None,
    format_result: Callable[[str], str] | None = None,
) -> None:
    """Register a tool function with the registry.

    Args:
        name: Tool name
        function: Tool function to call
        description: Human-readable description of what the tool does
        parameters: Parameters for the tool with type and description
        returns: Description of what the tool returns
        requires_confirmation: Whether the tool requires user confirmation
        confirmation_handler: Optional custom function to handle confirmation UI
            If provided, this function will be called instead of the default confirmation
            prompt. It should take the tool name, tool arguments, and an input function,
            and return True if the user confirms, False otherwise.
        format_result: Optional function to format the tool result for display
            Takes the raw result string and returns a formatted string for display
    """
    TOOLS[name] = {
        "function": function,
        "description": description,
        "parameters": parameters,
        "returns": returns,
        "requires_confirmation": requires_confirmation,
        "confirmation_handler": confirmation_handler,
        "format_result": format_result,
    }


def get_format_result(tool_name: str) -> Callable[[str], str] | None:
    """Get the format_result function for a tool.

    Args:
        tool_name: Name of the tool

    Returns:
        Format result function if registered, None otherwise
    """
    tool_info = TOOLS.get(tool_name)
    if tool_info:
        return tool_info.get("format_result")
    return None


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


def get_confirmation_handler(
    tool_name: str,
) -> Callable[[str, dict[str, Any], Callable[[str], str]], bool] | None:
    """Get the custom confirmation handler for a tool if one exists.

    Args:
        tool_name: Name of the tool

    Returns:
        The custom confirmation handler function if one exists, or None
    """
    if tool_name not in TOOLS:
        return None

    return TOOLS[tool_name].get("confirmation_handler")


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
