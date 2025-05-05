"""Tool execution and handling module."""

import json
from collections.abc import Callable
from typing import Any

from simple_agent.display import (
    display_error,
    display_info,
    format_tool_args,
    get_confirmation,
)
from simple_agent.tools import (
    execute_tool_call,
    get_confirmation_handler,
    get_tool_descriptions,
    requires_confirmation,
)


class ToolHandler:
    """Handles tool execution and user confirmation."""

    def __init__(self, input_func: Callable[[str], str] | None = None) -> None:
        """Initialize the tool handler.

        Args:
            input_func: Optional function to use for getting user input for confirmations
        """
        self.input_func = input_func or input

    def process_tool_calls(
        self,
        tool_calls: list[Any],
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Process a list of tool calls from the LLM.

        Args:
            tool_calls: List of tool calls to process
            messages: Current conversation context (will be updated)

        Returns:
            Updated messages with tool responses
        """
        # Create a working copy of the messages
        updated_messages = messages.copy()

        # Process each tool call
        for tool_call in tool_calls:
            # Parse the tool call
            tool_id = tool_call.id
            tool_name = tool_call.function.name

            try:
                # Parse arguments
                arguments = json.loads(tool_call.function.arguments)

                # Check if this tool requires confirmation
                # Skip confirmation for read operations and basic execute commands
                if tool_name == "execute_command" and "ls" in arguments.get(
                    "command", ""
                ):
                    requires_confirm = False
                else:
                    requires_confirm = requires_confirmation(tool_name)

                if requires_confirm:
                    # Check if the tool has a custom confirmation handler
                    custom_handler = get_confirmation_handler(tool_name)

                    if custom_handler:
                        # Use custom confirmation handler
                        confirmed = custom_handler(
                            tool_name, arguments, self.input_func
                        )
                    else:
                        # Use default confirmation handling
                        if self.input_func != input:
                            # For testing, use the provided input_func
                            args_string = format_tool_args(**arguments)
                            confirmation = self.input_func(
                                f"Confirm {tool_name}({args_string})? [Y/n] "
                            )

                            # Empty input (just Enter) defaults to yes
                            if confirmation == "":
                                confirmation = "y"

                            confirmed = confirmation.lower() in ["y", "yes"]
                        else:
                            # Use the standardized confirmation function from display module
                            args_string = format_tool_args(**arguments)
                            confirmed = get_confirmation(
                                f"<ansicyan>{tool_name}</ansicyan>({args_string})?"
                            )

                    if not confirmed:
                        # User rejected the tool call
                        display_info(
                            f"The user denied permission to execute {tool_name}"
                        )
                        tool_response = {
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "name": tool_name,
                            "content": "The user denied permission to execute this tool call.",
                        }
                        updated_messages.append(tool_response)
                        continue

                # Execute the tool - the tool implementation handles its own output
                result = execute_tool_call(tool_name, arguments)

                # Add tool response to messages
                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": str(result),
                }
                updated_messages.append(tool_response)
            except json.JSONDecodeError:
                error_message = "Invalid tool arguments"
                # Display error in the standard console
                display_error(error_message)

                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": "Error: Could not parse tool arguments.",
                }
                updated_messages.append(tool_response)

        return updated_messages

    def _format_value(self, value: Any) -> str:
        """Format a value for display to the user in a confirmation prompt.

        Args:
            value: The value to format

        Returns:
            Formatted string representation of the value
        """
        if isinstance(value, str) and len(value) > 100:
            # Truncate long strings
            return f"{value[:97]}..."
        return str(value)


def get_tools_for_llm() -> list[dict[str, Any]]:
    """Get the tools in a format ready for LLM API.

    Returns:
        List of tools formatted for LLM API
    """
    return get_tool_descriptions()
