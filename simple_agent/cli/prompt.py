"""Prompt Toolkit interface for Simple Agent."""

import os
from collections.abc import Callable

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import ANSI, HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style
from rich.console import Console

from simple_agent.cli.completion import CommandCompleter

# Help text for the CLI
HELP_TEXT = """
[bold]Simple Agent[/bold] - An AI assistant that can help with tasks

Just type your questions or requests naturally.
The agent can:
• Answer questions
• Run commands (when you ask it to)
• Read and write files (when you ask it to)

[bold]Commands:[/bold]
• [green]/help[/green]:  Show this help message
• [green]/clear[/green]: Clear the terminal screen
• [green]/exit[/green]:  Exit the agent

[bold]Input features:[/bold]
• End a line with [green]\\ [/green]for aligned multi-line input
• Use Tab key for command auto-completion

[bold]Response types:[/bold]
• [blue]Next action[/blue]: The agent knows what to do next and will continue automatically
• [yellow]Question[/yellow]: The agent needs more information from you
• Normal response: The task is complete
"""


def setup_keybindings() -> KeyBindings:
    """Set up key bindings for the prompt session."""
    kb = KeyBindings()

    @kb.add(Keys.ControlC)
    def _(event: KeyPressEvent) -> None:
        """Ctrl-C handler."""
        event.app.exit(exception=KeyboardInterrupt())

    @kb.add(Keys.ControlD)
    def _(event: KeyPressEvent) -> None:
        """Ctrl-D handler."""
        event.app.exit(exception=EOFError())

    @kb.add(Keys.Enter)
    def _(event: KeyPressEvent) -> None:
        """Enter key handler with special handling for backslash continuation."""
        # Get current buffer
        buffer = event.app.current_buffer

        # Check if the current line ends with a backslash
        current_line = buffer.document.current_line
        if current_line.endswith("\\"):
            # Remove the backslash
            buffer.delete_before_cursor(1)

            # Insert a newline (multiline mode will handle the indentation)
            buffer.newline()
            return

        # Normal Enter behavior
        buffer.validate_and_handle()

    return kb


class CLI:
    """Command-line interface for Simple Agent."""

    def __init__(
        self,
        process_input_callback: Callable[[str], None],
    ) -> None:
        """Initialize the CLI.

        Args:
            process_input_callback: Callback for processing user input
        """
        self.console = Console()
        self.process_input = process_input_callback

        # Set up prompt style
        self.style = Style.from_dict(
            {
                "prompt": "ansibrightyellow",
                "prompt.arrow": "ansiwhite",
                "continuation": "ansibrightblack",
                "user-input": "ansiwhite",
                # Completion menu colors - gray palette
                "completion-menu.completion": "bg:#444444 #ffffff",
                "completion-menu.completion.current": "bg:#666666 #ffffff",
                "completion-menu.meta.completion": "bg:#333333 #aaaaaa",
                "completion-menu.meta.completion.current": "bg:#555555 #ffffff",
                "completion-menu.multi-column-meta": "bg:#444444 #aaaaaa",
                # Scrollbar colors
                "scrollbar.background": "bg:#88aaaa",
                "scrollbar.button": "bg:#222222",
                # Highlighting for command syntax
                "command": "#aaccff",
                "special-command": "#ffcc00",
            }
        )

        # Try to set up history file in user's home directory
        history_file = os.path.expanduser("~/.simple_agent_history")
        try:
            history = FileHistory(history_file)
        except Exception:
            # Fall back to no history if file can't be created
            history = None

        # Create prompt session with advanced features
        self.session: PromptSession = PromptSession(
            history=history,
            auto_suggest=AutoSuggestFromHistory(),
            completer=CommandCompleter(),
            key_bindings=setup_keybindings(),
            style=self.style,
            complete_while_typing=True,
            complete_in_thread=True,  # Perform completion in a background thread
            mouse_support=True,  # Enable mouse support for selection
            wrap_lines=True,  # Wrap long lines
            multiline=True,  # Enable proper multiline support
            prompt_continuation=lambda width, line_number, is_soft_wrap: (
                "  " if not is_soft_wrap else ""
            ),
        )

    def show_help(self) -> None:
        """Display help information."""
        self.console.print(HELP_TEXT)

    def run_interactive_loop(self) -> None:
        """Run the interactive prompt loop."""
        # Display welcome message with styling
        welcome_message = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          🤖 Simple Agent           ┃
┃                                    ┃
┃ \033[32m/help\033[0m      \033[90m for available commands \033[1;37m┃
┃ \033[32m/clear\033[0m     \033[90m to clear the screen    \033[1;37m┃
┃ \033[32m/exit\033[0m      \033[90m to quit                \033[1;37m┃
┃ \033[32m\\ + Enter\033[0m  \033[90m to create a newline    \033[1;37m┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
        print_formatted_text(ANSI(f"\033[1;37m{welcome_message}\033[0m"))

        while True:
            try:
                # Get input from user with proper formatting and completions
                user_input = self.session.prompt(
                    HTML("<prompt.arrow>></prompt.arrow> "),
                    complete_in_thread=True,
                )

                # Skip empty input
                if not user_input.strip():
                    continue

                # Check for slash commands
                if user_input.lower() == "/exit":
                    print_formatted_text(
                        ANSI("\033[33mGoodbye! Exiting Simple Agent.\033[0m")
                    )
                    break
                elif user_input.lower() == "/help":
                    self.show_help()
                    continue
                elif user_input.lower() == "/clear":
                    clear()
                    continue

                # Process normal input
                self.process_input(user_input)

            except KeyboardInterrupt:
                print_formatted_text(ANSI("\n\033[33mInterrupted. Exiting.\033[0m"))
                break
            except EOFError:
                print_formatted_text(ANSI("\n\033[33mReceived EOF. Exiting.\033[0m"))
                break


def create_rich_formatted_response(response_json: dict) -> str:
    """Create a rich formatted response from JSON.

    Args:
        response_json: The parsed JSON response

    Returns:
        Formatted response string
    """
    formatted_output = []

    # Add the main message
    if "message" in response_json:
        formatted_output.append(response_json["message"])

    # Add status-specific formatting
    if "status" in response_json:
        status = response_json["status"]
        next_action = response_json.get("next_action")

        if status == "CONTINUE" and next_action:
            formatted_output.append(
                f"\n[bold blue]Next action:[/bold blue] {next_action}"
            )
        elif status == "ASK" and next_action:
            formatted_output.append(
                f"\n[bold yellow]Question:[/bold yellow] {next_action}"
            )

    return "\n".join(formatted_output)
