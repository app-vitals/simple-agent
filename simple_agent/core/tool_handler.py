"""Tool execution and handling module."""

import json
from collections.abc import Callable
from typing import Any

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.styles import Style
from rich.console import Console

from simple_agent.tools import (
    execute_tool_call,
    get_tool_descriptions,
    requires_confirmation,
)
from simple_agent.tools.utils import format_tool_args


class ToolHandler:
    """Handles tool execution and user confirmation."""

    def __init__(self, input_func: Callable[[str], str] | None = None) -> None:
        """Initialize the tool handler.

        Args:
            input_func: Optional function to use for getting user input for confirmations
        """
        self.console = Console()
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

                    # Use input_func for tests to work, otherwise use prompt_toolkit
                    if self.input_func != input:
                        # For testing, use the provided input_func
                        args_string = format_tool_args(**arguments)
                        confirmation = self.input_func(
                            f"Confirm {tool_name}({args_string})? [Y/n] "
                        )
                    else:
                        # Create a nice prompt_toolkit confirmation prompt
                        confirmation_style = Style.from_dict(
                            {
                                "tool": "ansibrightyellow bold",
                                "prompt": "ansiyellow",
                                "highlight": "ansibrightgreen",
                            }
                        )

                        # HTML-formatted prompt that highlights the tool name and includes arguments
                        # Use format_tool_args utility to format the arguments
                        args_string = format_tool_args(**arguments)
                        confirm_prompt = HTML(
                            f"<prompt>Confirm </prompt>"
                            f"<tool>{tool_name}({args_string})</tool>"
                            f"<prompt>? </prompt><highlight>[Y/n]</highlight> "
                        )

                        # Get confirmation using prompt_toolkit
                        confirmation = prompt(confirm_prompt, style=confirmation_style)

                    # Empty input (just Enter) defaults to yes
                    if confirmation == "":
                        confirmation = "y"

                    if confirmation.lower() not in ["y", "yes"]:
                        # User rejected the tool call
                        tool_response = {
                            "role": "tool",
                            "tool_call_id": tool_id,
                            "name": tool_name,
                            "content": "The user denied permission to execute this tool call.",
                        }
                        updated_messages.append(tool_response)
                        continue

                # Execute the tool
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
                self.console.print("[bold red]Error:[/bold red] Invalid tool arguments")
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
