"""Core agent loop implementation."""

import json
from collections.abc import Callable
from typing import Any

from rich.console import Console

from simple_agent.core.schema import AgentResponse, AgentStatus
from simple_agent.core.tool_handler import ToolHandler, get_tools_for_llm
from simple_agent.llm.client import LLMClient

HELP_TEXT = """
[bold]Simple Agent[/bold] - An AI assistant that can help with tasks

Just type your questions or requests naturally.
The agent can:
• Answer questions
• Run commands (when you ask it to)
• Read and write files (when you ask it to)

[bold]Special commands:[/bold]
• [green]continue[/green]: Continue with the next action the agent has planned
• [green]/help[/green]: Show this help message
• [green]/exit[/green]: Exit the agent

[bold]Response types:[/bold]
• [blue]Next action[/blue]: The agent knows what to do next and can continue automatically
• [yellow]Question[/yellow]: The agent needs more information from you
• Normal response: The task is complete
"""

SYSTEM_PROMPT = """You are Simple Agent, a command line assistant built on Unix philosophy principles.

Follow these core principles in all interactions:
- Do one thing well - Focus on the user's current request
- Simplicity over complexity - Provide direct, concise answers
- Modularity - Break down complex tasks into smaller steps
- Plain text - Communicate clearly in text format

You have the following tools available to assist users:
- read_files: Read contents of one or more files at once (can pass multiple files in a list)
- write_file: Write content to a file (requires user confirmation)
- patch_file: Replace specific content in a file (requires user confirmation)
- execute_command: Run a shell command (requires user confirmation)

For efficiency, always batch your file reads by using read_files with multiple file paths when you need to examine several files.

IMPORTANT: You MUST format all your responses as JSON following this schema:
{
  "message": "Your main message and analysis for the user",
  "status": "COMPLETE|CONTINUE|ASK",
  "next_action": "If status is CONTINUE, describe your next planned action. If status is ASK, formulate a question for the user."
}

Status values explanation:
- COMPLETE: Task is finished, no further action needed
- CONTINUE: You know what to do next and can proceed automatically 
- ASK: You need user input or permission to proceed

Example for a complete task:
{
  "message": "I've analyzed the README.md file and it shows this is a Python CLI project that implements a simple agent framework.",
  "status": "COMPLETE",
  "next_action": null
}

Example for an action you can continue with:
{
  "message": "I've listed the project files. This appears to be a Python CLI application.",
  "status": "CONTINUE",
  "next_action": "I'll read the README.md, main.py, and requirements.txt files to understand the project structure and dependencies."
}

Example for when you need user input:
{
  "message": "I can see several Python files in the project.",
  "status": "ASK",
  "next_action": "I could analyze the main code files together (main.py, utils.py, config.py) or focus on the tests first. Which would you prefer?"
}

When helping users:
- Focus on one task at a time
- Keep previous context in mind when the user says "continue" or similar
- Ask questions when clarification is needed, don't guess
- Keep responses concise and relevant
- Use available tools when appropriate
- Batch operations when possible (especially file reads) to improve efficiency
- ALWAYS ask permission before modifying files or running commands
- Respect the user's time and expertise
- Provide clear explanations of what tools will do before executing them"""


class Agent:
    """Simple agent that manages the conversation loop."""

    def __init__(self) -> None:
        """Initialize the agent."""
        # Initialize context with system prompt
        self.context: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}]
        self.console = Console()
        self.llm_client = LLMClient()
        self.tool_handler = ToolHandler()
        self.tools = get_tools_for_llm()

    def run(self, input_func: Callable[[str], str] | None = None) -> None:
        """Run the agent's main loop.

        Args:
            input_func: Function to use for getting input, defaults to built-in input
                        Useful for testing
        """
        # Set up input function for agent and tool handler
        if input_func is None:
            input_func = input

        # Update tool handler with input function
        self.tool_handler.input_func = input_func

        self.console.print(
            "[bold green]Simple Agent[/bold green] ready. Type '/exit' to quit. Type '/help' for help."
        )

        while True:
            # Get input from user with proper EOF (Ctrl+D) handling
            try:
                user_input = input_func("> ")
            except EOFError:
                # Handle Ctrl+D (EOF)
                print()  # Print newline for clean exit
                self.console.print("[yellow]Received EOF. Exiting.[/yellow]")
                break

            # Check for slash commands
            if user_input.lower() == "/exit":
                break

            # Process the user input
            self._process_input(user_input)

    def _process_input(self, user_input: str) -> None:
        """Process user input and generate a response.

        Args:
            user_input: The user's input text
        """
        # Check for slash commands first
        if user_input.lower() == "/help":
            self._show_help()
            return

        # Check for continuation command
        if user_input.lower() in ["continue", "proceed", "go on", "go ahead"]:
            # Look at the last assistant message to find the next action
            for msg in reversed(self.context):
                if msg.get("role") == "assistant":
                    try:
                        assistant_data = json.loads(msg.get("content", "{}"))
                        if (
                            "status" in assistant_data
                            and assistant_data["status"] == "CONTINUE"
                            and assistant_data.get("next_action")
                        ):
                            self.console.print(
                                f"[bold green]Continuing:[/bold green] {assistant_data['next_action']}"
                            )
                            # Create a more specific prompt based on the next_action
                            continuation_prompt = (
                                f"Please continue by {assistant_data['next_action']}"
                            )
                            self._handle_ai_request(continuation_prompt)
                            return
                    except (json.JSONDecodeError, KeyError):
                        pass

            # If we got here, we didn't find a clear continuation action
            self._handle_ai_request("Please continue from where you left off")
            return

        # Otherwise, treat as a regular AI request
        self._handle_ai_request(user_input)

    def _show_help(self) -> None:
        """Show help information."""
        self.console.print(HELP_TEXT)

    def _handle_ai_request(self, message: str) -> None:
        """Process a request through the AI model and handle tools if needed.

        Args:
            message: The user's message
        """
        # Update context with user message
        self.context.append({"role": "user", "content": message})

        # Process the request with tool call handling (using a loop)
        max_iterations = 20  # Prevent infinite loops
        iteration = 0

        while iteration < max_iterations:
            # Log the current step
            if iteration == 0:
                self.console.print("[bold]Processing...[/bold]")
            else:
                self.console.print(
                    f"[bold]Processing tool result (step {iteration})...[/bold]"
                )

            # Send to LLM
            response = self._send_llm_request(self.context)

            if not response:
                self.console.print(
                    "[bold red]Error:[/bold red] Failed to get a response"
                )
                return

            # Extract content and check for tool calls
            content, tool_calls = self.llm_client.get_message_content(response)

            # If there are no tool calls, we're done
            if not tool_calls:
                # Process and display the final response
                if content is not None:
                    self._process_llm_response(content, response)
                else:
                    self.console.print(
                        "[bold red]Error:[/bold red] Empty response from LLM"
                    )
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

        # If we've reached the maximum iterations, warn the user
        self.console.print(
            "[bold yellow]Warning:[/bold yellow] Maximum tool call iterations reached"
        )

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
            self.console.print("[bold red]Error:[/bold red] Empty response from LLM")
            return

        # Parse the JSON response
        try:
            # Parse the JSON content into our AgentResponse
            json_response = json.loads(content)
            structured_response = AgentResponse.model_validate(json_response)

            # Display the message to the user
            self.console.print(structured_response.message)

            # Handle the different statuses
            if structured_response.status == AgentStatus.CONTINUE:
                # Agent knows what to do next
                if structured_response.next_action:
                    self.console.print(
                        f"[bold blue]Next action:[/bold blue] {structured_response.next_action}"
                    )

                    # Continue with the next action
                    self.console.print(
                        f"[dim]Next Action: {structured_response.next_action}[/dim]"
                    )
                    continuation_prompt = (
                        f"Please continue by {structured_response.next_action}"
                    )
                    self._handle_ai_request(continuation_prompt)

            elif (
                structured_response.status == AgentStatus.ASK
                and structured_response.next_action
            ):
                # Agent needs user input
                self.console.print(
                    f"[bold yellow]Question:[/bold yellow] {structured_response.next_action}"
                )

            # Keep the raw JSON response in the context for the LLM
            self.context.append({"role": "assistant", "content": content})

        except json.JSONDecodeError:
            # Fallback for non-JSON responses
            self.console.print(content)
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
