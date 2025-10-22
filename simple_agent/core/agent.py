"""Core agent loop implementation."""

import json
import time
from collections.abc import Callable
from typing import Any

from simple_agent.cli.prompt import CLI, CLIMode
from simple_agent.context.extractor import ContextExtractor
from simple_agent.core.schema import AgentResponse
from simple_agent.core.tool_handler import ToolHandler, get_tools_for_llm
from simple_agent.display import (
    console,
    display_error,
    display_response,
    display_status_message,
    display_warning,
)
from simple_agent.live_console import live_context, set_stage_message
from simple_agent.llm.client import LLMClient

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
- Users can add context via /context command (you'll see this in conversation)
- Context includes: manual notes, calendar events, tasks, time tracking, files worked on
- When asked "what should I work on next?" or similar, consider all available context
- Provide reasoning based on time availability, priorities, and current focus

IMPORTANT: You MUST format all your responses as JSON following this schema:
{
  "message": "Your main message and analysis for the user",
  "status": "COMPLETE|ASK",
  "question": "If status is ASK, formulate a question for the user."
}

Status values explanation:
- COMPLETE: Task is finished, no further action needed
- CONTINUE: You know what to do next and can proceed automatically 
- ASK: You need user input or permission to proceed

Example for a complete task:
{
  "message": "I've analyzed the README.md file and it shows this is a Python CLI project that implements a simple agent framework.",
  "status": "COMPLETE",
  "question": null
}

Example for when you need user input:
{
  "message": "I can see several Python files in the project.",
  "status": "ASK",
  "question": "I could analyze the main code files together (main.py, utils.py, config.py) or focus on the tests first. Which would you prefer?"
}

When helping users:
- Focus on one task at a time
- Keep previous context in mind when the user says "continue" or similar
- Ask questions when clarification is needed, don't guess
- Keep responses concise and relevant
- Use available tools when appropriate
- Do not ask permission to use tools, the system will handle that
- Batch operations when possible (especially file reads) to improve efficiency
- Respect the user's time and expertise
- Provide clear explanations of what tools will do before executing them"""


class Agent:
    """Simple agent that manages the conversation loop."""

    def __init__(self) -> None:
        """Initialize the agent."""
        # Initialize context with system prompt
        self.context: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.llm_client = LLMClient()
        self.tool_handler = ToolHandler()
        self.tools = get_tools_for_llm()
        self.request_start_time: float | None = None
        self.context_extractor = ContextExtractor(llm_client=self.llm_client)

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
        # Update context with user message
        self.context.append({"role": "user", "content": message})
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

                # Send to LLM
                response = self._send_llm_request(self.context)

                if not response:
                    display_error("Failed to get a response")
                    return

                # Extract content and check for tool calls
                content, tool_calls = self.llm_client.get_message_content(response)

                # If there are no tool calls, we're done
                if not tool_calls:
                    # Exit the live context before processing the final response
                    live.stop()
                    # Process and display the final response
                    if content is not None:
                        self._process_llm_response(content, response)
                    else:
                        display_error("Empty response from LLM")

                    # Extract context from this interaction
                    self._extract_context()
                    return

                # Handle tool calls
                # Add the assistant's response with tool calls to context
                assistant_message = {"role": "assistant"}
                assistant_message.update(response.choices[0].message.model_dump())
                self.context.append(assistant_message)

                # Process tool calls
                self.context = self.tool_handler.process_tool_calls(
                    tool_calls, self.context
                )

                # Increment iteration counter
                iteration += 1

            # Exit the live context before displaying warning
            live.stop()

            # If we've reached the maximum iterations, warn the user
            display_warning("Maximum tool call iterations reached")

        # Extract context from this interaction (after live context exits)
        self._extract_context()

    def _extract_context(self) -> None:
        """Extract and store context from the recent interaction."""
        try:
            # Extract context from the conversation messages
            self.context_extractor.extract_from_messages(self.context)
        except Exception as e:
            # Show warning but don't crash
            display_warning(f"Context extraction failed: {e}")

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
            response_format=AgentResponse,
        )

    def _process_llm_response(self, content: str, response: Any) -> None:
        """Process and display the LLM response.

        Args:
            content: The text content from the LLM
            response: The full response object
        """
        if not content:
            display_error("Empty response from LLM")
            return

        # Parse the JSON response
        try:
            # Parse the JSON content into our AgentResponse
            json_response = json.loads(content)
            structured_response = AgentResponse.model_validate(json_response)

            # Display the response using our helper
            display_response(
                structured_response.message,
                structured_response.status.value,
                structured_response.question,
            )

            # Keep the raw JSON response in the context for the LLM
            self.context.append({"role": "assistant", "content": content})

        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            display_warning("LLM response was not in expected JSON format")
            console.print(f"[dim]{content}[/dim]")
            self.context.append({"role": "assistant", "content": content})

        # Manage context size - keep at most 10 messages
        if len(self.context) > 10:
            # Keep the most recent messages, preserving system message if present
            start_idx = 1 if self.context and self.context[0]["role"] == "system" else 0
            self.context = (
                self.context[0:1] + self.context[-9:]
                if start_idx == 1
                else self.context[-10:]
            )
