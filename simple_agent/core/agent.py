"""Core agent loop implementation."""

import contextlib
import json
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any

from rich.markdown import Markdown

from simple_agent.cli.prompt import CLI, CLIMode
from simple_agent.config import config
from simple_agent.context.compression_prompt import get_compression_prompt
from simple_agent.context.loader import load_context_from_directory
from simple_agent.core.tool_handler import ToolHandler, get_tools_for_llm
from simple_agent.display import (
    display_error,
    display_info,
    display_status_message,
    display_warning,
    format_tool_args,
    print_with_padding,
)
from simple_agent.live_console import console, live_context, set_stage_message
from simple_agent.llm.client import LLMClient
from simple_agent.messages import MessageManager
from simple_agent.tools.mcp.adapter import MCPToolAdapter
from simple_agent.tools.mcp.manager import MCPServerManager
from simple_agent.tools.registry import get_format_result

SYSTEM_PROMPT = """You are Simple Agent, a command line execution efficiency assistant built on Unix philosophy principles.

Your primary role is to help users optimize their daily execution by:
- Providing context-aware assistance for task prioritization
- Understanding the user's current work context (files, calendar, tasks, time tracking)
- Helping determine "what to work on next" based on available context
- Assisting with file operations, command execution, and code tasks

Follow these core principles in all interactions:
- Do one thing well - Focus on the user's current request
- Simplicity over complexity - Provide direct, concise answers
- Modularity - Break down complex tasks into smaller steps
- Plain text - Communicate clearly in text format
- Context awareness - Consider available context when making recommendations

You have the following tools available to assist users:
- read_files: Read contents of one or more files at once (can pass multiple files in a list)
- write_file: Write content to a file (requires user confirmation)
- patch_file: Replace specific content in a file (requires user confirmation)
- execute_command: Run a shell command (requires user confirmation)

For efficiency, always batch your file reads by using read_files with multiple file paths when you need to examine several files.

Context System:
- Context is automatically extracted from user interactions and tool usage
- Context includes: manual notes, calendar events, tasks, time tracking, files worked on
- When asked "what should I work on next?" or similar, consider all available context
- Provide reasoning based on time availability, priorities, and current focus

When helping users:
- Focus on one task at a time
- Keep previous context in mind when the user says "continue" or similar
- Ask questions when clarification is needed, don't guess
- Keep responses concise and relevant
- Use available tools when appropriate
- Do not ask permission to use tools, the system will handle that
- Batch operations when possible (especially file reads) to improve efficiency
- Respect the user's time and expertise
- Provide clear explanations alongside your tool usage"""


class Agent:
    """Simple agent that manages the conversation loop."""

    def __init__(self) -> None:
        """Initialize the agent."""
        self.llm_client = LLMClient()
        self.tool_handler = ToolHandler()
        self.request_start_time: float | None = None

        # Initialize MCP servers if configured and not disabled
        self.mcp_manager: MCPServerManager | None = None
        self.mcp_adapter: MCPToolAdapter | None = None
        self.mcp_errors: dict[str, str] = {}  # Track server load errors
        if config.mcp_servers and not config.mcp_disabled:
            try:
                self.mcp_manager = MCPServerManager(config.mcp_servers)
                self.mcp_adapter = MCPToolAdapter(self.mcp_manager)
                self._load_mcp_tools()
            except Exception as e:
                display_warning("Failed to initialize MCP servers", e)

        # Get all tools (now includes MCP tools if loaded)
        self.tools = get_tools_for_llm()

        # Initialize message manager and load previous messages
        self.messages = MessageManager(max_messages=50)
        self.messages.load()

    def _load_mcp_tools(self) -> None:
        """Start all configured MCP servers and register their tools."""
        if not self.mcp_manager or not self.mcp_adapter:
            return

        for server_name in config.mcp_servers:
            try:
                # Start server and discover tools
                self.mcp_manager.start_server_sync(server_name)
                self.mcp_adapter.discover_and_register_tools_sync(server_name)
            except Exception as e:
                # Track error and log warning but continue - don't fail agent startup
                self.mcp_errors[server_name] = str(e)
                display_warning(f"Failed to load MCP server '{server_name}'", e)

    def __del__(self) -> None:
        """Cleanup MCP servers on agent destruction."""
        if self.mcp_manager:
            with contextlib.suppress(Exception):
                self.mcp_manager.shutdown_all_sync()

    def _build_system_prompt(self) -> str:
        """Build the system prompt with current context injected.

        Returns:
            System prompt with recent context included
        """
        # Start with base prompt and add current date
        today = datetime.now().strftime("%Y-%m-%d")
        prompt = f"Today's date: {today}\n\n{SYSTEM_PROMPT}"

        # Load markdown context from context/*.md files
        context = load_context_from_directory()

        # Only inject context if there is some
        if context:
            # Add a section with current context
            prompt += f"\n\n## Current Context\n\n{context}\n\n"
            prompt += """Use this context to provide more relevant and personalized assistance:
- When asked "what should I work on next?", reference this context
- Consider time constraints and deadlines
- Be aware of current projects, goals, and decisions
- Suggest next steps that align with recent work patterns"""

        return prompt

    def _display_loaded_messages(self) -> None:
        """Display previously loaded conversation messages on startup."""
        if len(self.messages) == 0:
            return

        # Show count of loaded messages
        message_count = len(self.messages)
        display_info(f"Resuming conversation ({message_count} messages loaded)\n")

        # Display each message
        prev_role = None
        for msg in self.messages.get_all():
            role = msg.get("role", "unknown")
            content = msg.get("content", "")

            # Add spacing between different message types
            # Exception: no spacing between assistant (with tool calls) and tool results
            should_add_spacing = prev_role is not None and prev_role != role
            if should_add_spacing and not (prev_role == "assistant" and role == "tool"):
                print_with_padding("", newline_before=False)

            if role == "user":
                # Display user messages without padding (they already have ">")
                console.print(f"> {content}")
            elif role == "assistant":
                # Check if this message has tool calls
                tool_calls = msg.get("tool_calls")
                if tool_calls:
                    # Display tool calls with arguments
                    for tool_call in tool_calls:
                        function = tool_call.get("function", {})
                        tool_name = function.get("name", "unknown")
                        arguments_str = function.get("arguments", "{}")

                        # Parse arguments and format them
                        try:
                            args = json.loads(arguments_str)
                            args_formatted = format_tool_args(**args)
                            print_with_padding(
                                f"[cyan]{tool_name}[/cyan]({args_formatted})",
                                newline_before=False,
                            )
                        except (json.JSONDecodeError, TypeError):
                            # Fallback if arguments can't be parsed
                            print_with_padding(
                                f"[cyan]{tool_name}[/cyan](...)",
                                newline_before=False,
                            )
                elif content:
                    # Display assistant messages with markdown
                    print_with_padding(Markdown(content), newline_before=False)
            elif role == "tool":
                # Display tool results
                tool_content = msg.get("content", "")
                tool_name = msg.get("name", "")
                if tool_content:
                    # Get the tool's format function if available
                    format_func = get_format_result(tool_name)
                    if format_func:
                        formatted_result = format_func(tool_content)
                    else:
                        # Generic formatting: just detect errors
                        content_lower = str(tool_content).lower()
                        if "error" in content_lower or "failed" in content_lower:
                            formatted_result = "[red]✗ Failed[/red]"
                        else:
                            formatted_result = "[dim]✓ Completed[/dim]"

                    print_with_padding(formatted_result, newline_before=False)

            prev_role = role

        # Add final spacing
        print_with_padding("", newline_before=False)

    def run(self, input_func: Callable[[str], str] | None = None) -> None:
        """Run the agent's main loop using prompt_toolkit.

        Args:
            input_func: Function to use for getting input, only used for testing
        """
        # Update tool handler with input function (only used in testing)
        if input_func is not None:
            self.tool_handler.input_func = input_func

        # Create CLI instance with callback to process input
        self.cli = CLI(
            process_input_callback=self._process_input,
            on_start_callback=self._display_loaded_messages,
            message_manager=self.messages,
            mcp_manager=self.mcp_manager,
            mcp_errors=self.mcp_errors,
        )

        # Run the interactive prompt loop
        self.cli.run_interactive_loop()

    def _process_input(self, user_input: str) -> None:
        """Process user input and generate a response.

        Args:
            user_input: The user's input text
        """
        try:
            self.request_start_time = time.monotonic()

            # Check if this is a compression request
            if user_input.startswith("__COMPRESS__"):
                # Extract optional user instructions
                instructions = user_input[len("__COMPRESS__") :].strip()
                self._handle_compression(instructions)
            else:
                self._handle_ai_request(user_input)

            self.request_start_time = None
        except KeyboardInterrupt:
            # Handle Ctrl+C gracefully
            display_warning("Interrupted by user...")

    def _get_status_message(self) -> str:
        # Calculate elapsed time
        current_elapsed: float | None = None
        if self.request_start_time is not None:
            # Calculate elapsed time since request started
            current_elapsed = time.monotonic() - self.request_start_time
        # Get token counts and cost from LLM client
        tokens_sent, tokens_received, completion_cost = (
            self.llm_client.get_token_counts()
        )
        return display_status_message(
            tokens_sent, tokens_received, current_elapsed, completion_cost
        )

    def _handle_ai_request(self, message: str) -> None:
        """Process a request through the AI model and handle tools if needed.

        Args:
            message: The user's message
        """
        # Add user message to history
        self.messages.append({"role": "user", "content": message})
        if self.cli.mode != CLIMode.NORMAL:
            return

        # Process the request with tool call handling (using a loop)
        max_iterations = 20  # Prevent infinite loops
        iteration = 0

        # Use the live context with dynamic status updates
        with live_context(
            status_callback=self._get_status_message, update_interval=0.1
        ) as live:
            while iteration < max_iterations:
                # Update stage message based on current iteration
                if iteration == 0:
                    set_stage_message("Analyzing request...")
                else:
                    set_stage_message("Processing tools...")

                # Build message list with fresh system prompt
                messages_for_llm = self.messages.build_for_llm(
                    self._build_system_prompt()
                )

                # Send to LLM
                response = self._send_llm_request(messages_for_llm)

                if not response:
                    display_error("Failed to get a response")
                    return

                # Extract content and check for tool calls
                content, tool_calls = self.llm_client.get_message_content(response)

                # If there are no tool calls, we're done
                if not tool_calls:
                    # Update stage to show completion
                    set_stage_message("Complete")
                    time.sleep(0.12)
                    # Exit the live context before displaying response
                    live.stop()
                    # Display the final response
                    if content:
                        # Print with padding and an extra line at the end
                        print_with_padding(Markdown(content), extra_line=True)
                        # Add to messages
                        self.messages.append({"role": "assistant", "content": content})
                    else:
                        display_error("Empty response from LLM")

                    return

                # Display any text content alongside tool calls
                if content:
                    print_with_padding(
                        Markdown(content), style="dim", newline_before=True
                    )

                # Handle tool calls
                # Add the assistant's response with tool calls to messages
                assistant_message = {"role": "assistant"}
                assistant_message.update(response.choices[0].message.model_dump())
                self.messages.append(assistant_message)

                # Process tool calls and get updated message list
                updated_messages = self.tool_handler.process_tool_calls(
                    tool_calls, self.messages.get_all()
                )

                # Update messages with tool results (replace all non-system messages)
                # Clear current messages and add back the updated ones
                self.messages.clear()
                self.messages.extend(updated_messages)

                # Increment iteration counter
                iteration += 1

            # Exit the live context before displaying warning
            live.stop()

            # If we've reached the maximum iterations, warn the user
            display_warning("Maximum tool call iterations reached")

    def _handle_compression(self, user_instructions: str = "") -> None:
        """Handle compression of conversation to context files.

        Args:
            user_instructions: Optional user-provided compression instructions
        """
        # Get the full conversation history
        conversation_history = self.messages.get_all()

        if not conversation_history:
            display_info("No conversation to compress.")
            return

        display_info("Starting compression workflow...")

        # Build compression messages
        compression_messages = get_compression_prompt(
            conversation_history=conversation_history,
            user_instructions=user_instructions,
        )

        # Process compression with tool calls (similar to _handle_ai_request)
        max_iterations = 20
        iteration = 0

        # Use the live context with dynamic status updates
        with live_context(
            status_callback=self._get_status_message, update_interval=0.1
        ) as live:
            while iteration < max_iterations:
                # Update stage message based on current iteration
                if iteration == 0:
                    set_stage_message("Reviewing conversation...")
                else:
                    set_stage_message("Updating context files...")

                # Send to LLM
                response = self._send_llm_request(compression_messages)

                if not response:
                    display_error("Failed to get compression response")
                    return

                # Extract content and check for tool calls
                content, tool_calls = self.llm_client.get_message_content(response)

                # If there are no tool calls, compression is done
                if not tool_calls:
                    # Update stage to show completion
                    set_stage_message("Complete")
                    time.sleep(0.12)
                    # Exit the live context before displaying response
                    live.stop()

                    # Display the final response
                    if content:
                        print_with_padding(Markdown(content), extra_line=True)

                    # Clear the conversation messages after successful compression
                    display_info("Clearing conversation history...")
                    self.messages.clear()
                    display_info("Compression complete!")
                    return

                # Display any text content alongside tool calls
                if content:
                    print_with_padding(
                        Markdown(content), style="dim", newline_before=True
                    )

                # Handle tool calls
                # Add the assistant's response with tool calls to compression messages
                assistant_message = {"role": "assistant"}
                assistant_message.update(response.choices[0].message.model_dump())
                compression_messages.append(assistant_message)

                # Process tool calls and get updated message list
                updated_messages = self.tool_handler.process_tool_calls(
                    tool_calls, compression_messages
                )

                # Update compression messages with tool results
                compression_messages = updated_messages

                # Increment iteration counter
                iteration += 1

            # Exit the live context before displaying warning
            live.stop()

            # If we've reached the maximum iterations, warn the user
            display_warning("Maximum compression iterations reached")

    def _send_llm_request(self, messages: list[dict]) -> Any | None:
        """Send a request to the LLM.

        Args:
            messages: The conversation context

        Returns:
            The LLM response object or None if an error occurs
        """
        return self.llm_client.send_completion(
            messages=messages,
            tools=self.tools,
        )
