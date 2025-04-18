"""LLM client for model integration."""

import json
from collections.abc import Callable
from typing import Any

import litellm
from rich.console import Console

from simple_agent.config import config
from simple_agent.core.schema import AgentResponse
from simple_agent.tools import (
    execute_tool_call,
    get_tool_descriptions,
    requires_confirmation,
)


class LLMClient:
    """Client for interacting with Large Language Model APIs."""

    def __init__(self, api_key: str | None = None) -> None:
        """Initialize the LLM client.

        Args:
            api_key: Optional API key, if not provided will look for an environment variable
        """
        self.console = Console()
        self.api_key = api_key or config.llm.api_key
        self.tools = get_tool_descriptions()

        # Configure LiteLLM
        litellm.drop_params = True  # Don't send unnecessary params

    def send_message(
        self,
        message: str,
        context: list[dict] | None = None,
        input_func: Callable[[str], str] | None = None,
    ) -> str | None:
        """Send a message to the AI model API.

        Args:
            message: The message to send
            context: Optional conversation context
            input_func: Optional function to use for getting user input (for confirmations)

        Returns:
            The model's response, or None if an error occurs
        """
        if not self.api_key:
            self.console.print("[bold red]Error:[/bold red] No API key provided")
            return None

        try:
            # Create messages format
            messages = context.copy() if context else []
            messages.append({"role": "user", "content": message})

            # Call the model using config with structured response format
            response = litellm.completion(
                model=config.llm.model,
                messages=messages,
                tools=self.tools,
                tool_choice="auto",
                response_format=AgentResponse,  # Use Pydantic model directly
                api_key=self.api_key,
            )

            # Check if there's a tool call in the response
            message_content = response.choices[0].message

            if hasattr(message_content, "tool_calls") and message_content.tool_calls:
                # Handle tool calls
                return self._handle_tool_calls(message_content, messages, input_func)
            else:
                # Extract and return the regular text response
                content = message_content.content
                if content is None:
                    return None
                return str(content)
        except Exception as e:
            self.console.print(f"[bold red]API Error:[/bold red] {e}")
            return None

    def _handle_tool_calls(
        self,
        message_content: Any,
        messages: list[dict[str, Any]],
        input_func: Callable[[str], str] | None = None,
    ) -> str:
        """Handle any tool calls from the LLM.

        Args:
            message_content: The message content with tool calls
            messages: The conversation history
            input_func: Optional function to use for getting user input for confirmations

        Returns:
            The final response after tool execution
        """
        # Add assistant's tool call message to context
        assistant_message = {"role": "assistant"}
        assistant_message.update(message_content.model_dump())
        messages.append(assistant_message)

        # Process each tool call
        for tool_call in message_content.tool_calls:
            # Parse the tool call
            tool_id = tool_call.id
            tool_name = tool_call.function.name

            try:
                # Parse arguments
                arguments = json.loads(tool_call.function.arguments)

                # Check if this tool requires confirmation
                requires_confirm = requires_confirmation(tool_name)

                if requires_confirm:
                    # Format arguments for user-friendly display
                    args_display = "\n".join(
                        [
                            f"  - {k}: {self._format_value(v)}"
                            for k, v in arguments.items()
                        ]
                    )

                    # Ask for confirmation
                    self.console.print(
                        f"\n[bold yellow]Tool call requested:[/bold yellow] {tool_name}"
                    )
                    self.console.print(f"[yellow]Arguments:[/yellow]\n{args_display}")

                    # Use provided input_func or use console prompt with proper formatting
                    if input_func:
                        confirmation = input_func("Confirm execution? (Y/n) ")
                    else:
                        # Rich console properly handles the formatting
                        self.console.print(
                            "[yellow]Confirm execution? (Y/n)[/yellow]", end=" "
                        )
                        confirmation = input()

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
                        messages.append(tool_response)
                        continue

                # Execute the tool
                self.console.print(
                    f"[bold blue]Executing tool:[/bold blue] {tool_name}"
                )
                result = execute_tool_call(tool_name, arguments)

                # Add tool response to messages
                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": str(result),
                }
                messages.append(tool_response)
            except json.JSONDecodeError:
                self.console.print("[bold red]Error:[/bold red] Invalid tool arguments")
                tool_response = {
                    "role": "tool",
                    "tool_call_id": tool_id,
                    "name": tool_name,
                    "content": "Error: Could not parse tool arguments.",
                }
                messages.append(tool_response)

        # Get final response after tool execution
        try:
            final_response = litellm.completion(
                model=config.llm.model,
                messages=messages,
                tools=self.tools,
                api_key=self.api_key,
                response_format=AgentResponse,  # Use Pydantic model directly
            )

            content = final_response.choices[0].message.content
            if content is None:
                return "Error: No response received after tool execution."
            return str(content)
        except Exception as e:
            self.console.print(
                f"[bold red]API Error (after tool execution):[/bold red] {e}"
            )
            return f"Error getting response after tool execution: {str(e)}"

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
