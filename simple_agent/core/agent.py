"""Core agent loop implementation."""

from collections.abc import Callable

from rich.console import Console

from simple_agent.llm.client import LLMClient


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
            "[bold green]Simple Agent[/bold green] ready. Type 'exit' to quit."
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

            if user_input.lower() == "exit":
                break

            # Process the user input
            self._process_input(user_input)

    def _process_input(self, user_input: str) -> None:
        """Process user input and generate a response.

        Args:
            user_input: The user's input text
        """
        # Simple processing for now - will be expanded
        self.console.print(f"Received: {user_input}")
