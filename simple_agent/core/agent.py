"""Core agent loop implementation."""

from collections.abc import Callable

from rich.console import Console

from simple_agent.llm.client import LLMClient

HELP_TEXT = """
[bold]Simple Agent[/bold] - An AI assistant that can help with tasks

Just type your questions or requests naturally.
The agent can:
• Answer questions
• Run commands (when you ask it to)
• Read and write files (when you ask it to)

[bold]Special commands:[/bold]
• [green]/help[/green]: Show this help message
• [green]/exit[/green]: Exit the agent
"""


class Agent:
    """Simple agent that manages the conversation loop."""

    def __init__(self) -> None:
        """Initialize the agent."""
        self.context: list[dict] = []
        self.console = Console()
        self.llm_client = LLMClient()

    def run(self, input_func: Callable[[str], str] | None = None) -> None:
        """Run the agent's main loop.

        Args:
            input_func: Function to use for getting input, defaults to built-in input
                        Useful for testing
        """
        if input_func is None:
            input_func = input

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

        # Otherwise, treat as an AI request
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

        # Send to LLM
        self.console.print("[bold]Processing...[/bold]")
        response = self.llm_client.send_message(message, self.context)

        if not response:
            self.console.print("[bold red]Error:[/bold red] Failed to get a response")
            return

        # Display the AI response
        self.console.print(response)

        # Update context with AI response
        self.context.append({"role": "assistant", "content": response})

        # Manage context size - keep at most 10 messages
        if len(self.context) > 10:
            # Keep the most recent messages, preserving system message if present
            start_idx = 1 if self.context and self.context[0]["role"] == "system" else 0
            self.context = (
                self.context[0:1] + self.context[-9:]
                if start_idx == 1
                else self.context[-10:]
            )
