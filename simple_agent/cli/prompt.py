"""Prompt Toolkit interface for Simple Agent."""

import os
from collections.abc import Callable
from enum import Enum

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style

from simple_agent.cli.completion import Completer
from simple_agent.context import get_context_manager
from simple_agent.display import (
    console,
    display_error,
    display_exit,
    display_warning,
)
from simple_agent.tools import execute_command


class CLIMode(Enum):
    """CLI interaction modes."""

    NORMAL = "normal"
    SHELL = "shell"


# Define prompt components
NORMAL_PROMPT = HTML("<prompt.arrow>></prompt.arrow> ")
SHELL_PROMPT = HTML("<prompt.arrow>!</prompt.arrow> ")


def setup_keybindings(cli: "CLI") -> KeyBindings:
    """Set up key bindings for the prompt session.

    Args:
        cli: The CLI instance to bind keys for

    Returns:
        KeyBindings instance with configured key bindings
    """
    kb = KeyBindings()

    @kb.add(Keys.ControlC)
    def _(event: KeyPressEvent) -> None:
        """Ctrl-C handler that clears input or exits."""
        # Get buffer
        buffer = event.app.current_buffer

        # If there is nothing to clear, exit the application
        if cli.mode == CLIMode.NORMAL and not buffer.text:
            event.app.exit(exception=KeyboardInterrupt())

        # Clear the buffer
        buffer.text = ""

        # Reset to normal mode
        cli.set_mode(CLIMode.NORMAL)

    @kb.add(Keys.ControlD)
    def _(event: KeyPressEvent) -> None:
        """Ctrl-D handler."""
        event.app.exit(exception=EOFError())

    @kb.add("!")
    def _(event: KeyPressEvent) -> None:
        # Get buffer
        buffer = event.app.current_buffer

        if buffer.text:
            # If there's already text, insert a "!" at the cursor position
            buffer = event.current_buffer
            buffer.insert_text("!")
            return

        if cli.set_mode(CLIMode.SHELL):
            return

        # If we're in shell mode, insert a "!" at the cursor position
        buffer = event.current_buffer
        buffer.insert_text("!")
        return

    @kb.add(Keys.Backspace)
    def _(event: KeyPressEvent) -> None:
        """Backspace handler to reset mode when buffer is empty."""
        buffer = event.app.current_buffer

        # If buffer is empty and we're in shell mode, reset to normal mode
        if buffer.cursor_position == 0 and cli.set_mode(CLIMode.NORMAL):
            return

        # Let the backspace perform its normal function
        buffer.delete_before_cursor(1)

    @kb.add(Keys.Enter)
    def _(event: KeyPressEvent) -> None:
        """Enter key handler with special handling for backslash continuation."""
        # Get current buffer
        buffer = event.app.current_buffer

        # Check if the current line ends with a backslash
        current_line = buffer.document.current_line
        if current_line.endswith("\\"):
            # Remove the backslash
            if cli.mode == CLIMode.NORMAL:
                buffer.delete_before_cursor(1)

            # Insert a newline (multiline mode will handle the indentation)
            buffer.newline()
            return

        # Normal Enter behavior
        buffer.validate_and_handle()

    return kb


# Help text for the CLI
HELP_TEXT = """
[bold]Simple Agent[/bold] - Command line execution efficiency assistant

Built on Unix philosophy principles to help optimize your daily execution.

[bold]What I can help with:[/bold]
• Execute shell commands and scripts
• Read and analyze files
• Search for files and patterns
• Remember context from your conversations

[bold]Commands:[/bold]
• [green]/help[/green]:          Show this help message
• [green]/clear[/green]:         Clear the terminal screen
• [green]/show-context[/green]:  View recent context
• [green]/clear-context[/green]: Clear stored context
• [green]/exit[/green]:          Exit the agent
• [green]![/green]:              Run a shell command directly

[bold]Input features:[/bold]
• End a line with [green]\\ [/green]for aligned multi-line input
• Use Tab key for command auto-completion

Just type your requests naturally and I'll help you get things done.
"""


class CLI:
    """Interactive CLI for Simple Agent."""

    def __init__(
        self,
        process_input_callback: Callable[[str], None],
    ) -> None:
        """Initialize the CLI.

        Args:
            process_input_callback: Callback for processing user input
        """
        self.process_input = process_input_callback
        self.mode = CLIMode.NORMAL

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
            completer=Completer(),
            key_bindings=setup_keybindings(self),
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
        console.print(HELP_TEXT)

    def show_context(self) -> None:
        """Display current context."""
        context_manager = get_context_manager()
        entries = context_manager.get_context(max_age_hours=24, limit=50)

        if not entries:
            console.print("[dim]No recent context available.[/dim]")
            return

        console.print("\n[bold cyan]Recent Context (last 24 hours):[/bold cyan]\n")

        # Group by type
        by_type: dict[str, list[tuple[str, str]]] = {}
        for entry in entries:
            type_name = entry.type.value.replace("_", " ").title()
            if type_name not in by_type:
                by_type[type_name] = []
            # Format timestamp
            time_str = entry.timestamp.strftime("%H:%M")
            by_type[type_name].append((time_str, entry.content))

        # Display each type
        for type_name, items in by_type.items():
            console.print(f"[bold]{type_name}:[/bold]")
            for time_str, content in items[:10]:  # Max 10 per type
                console.print(f"  [dim]{time_str}[/dim] {content}")
            console.print()

    def clear_context(self) -> None:
        """Clear all stored context."""
        context_manager = get_context_manager()
        count = context_manager.clear_context()
        console.print(f"[green]Cleared {count} context entries.[/green]")

    def set_mode(self, mode: CLIMode) -> bool:
        """Set the current interaction mode.

        Args:
            mode: The mode to switch to

        Returns:
            True if successful, False otherwise
        """
        if self.mode == mode:
            return False
        self.mode = mode
        if self.mode == CLIMode.NORMAL:
            self.session.message = NORMAL_PROMPT
        elif self.mode == CLIMode.SHELL:
            self.session.message = SHELL_PROMPT
        else:
            raise ValueError(f"Invalid mode: {mode}")
        self.session.app.invalidate()
        return True

    def run_interactive_loop(self) -> None:
        """Run the interactive prompt loop."""
        # Display welcome message with styling
        welcome_message = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          🤖 Simple Agent              ┃
┃                                        ┃
┃ /help           for available commands ┃
┃ /clear          clear the screen       ┃
┃ /show-context   view recent context    ┃
┃ /clear-context  reset context          ┃
┃ /exit           to quit                ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
        # Using direct console.print since we want custom formatting for the welcome box
        console.print(f"[bold white]{welcome_message}[/bold white]")

        while True:
            try:
                # Get input from user with proper formatting and completions
                user_input = self.session.prompt(
                    NORMAL_PROMPT,
                    complete_in_thread=True,
                )

                # Skip empty input
                if not user_input.strip():
                    continue

                # Check for slash commands
                if user_input.lower() == "/exit":
                    display_exit("Goodbye! Simple Agent shutting down")
                    break
                elif user_input.lower() == "/help":
                    self.show_help()
                    continue
                elif user_input.lower() == "/clear":
                    clear()
                    continue
                elif user_input.lower() == "/show-context":
                    self.show_context()
                    continue
                elif user_input.lower() == "/clear-context":
                    self.clear_context()
                    continue
                elif user_input.startswith("/"):
                    # Handle unknown slash commands
                    display_warning(f"Unknown command: {user_input}")
                    continue

                if self.mode == CLIMode.SHELL:
                    # Execute the command
                    stdout, stderr, return_code = execute_command(user_input)

                    # Format combined input for the agent context
                    context_message = f"Command:\n```bash\n$ {user_input}\n```\nOutput:\n```\n{stdout}\n{stderr}\n```\nReturn code: {return_code}\n"

                    # Process the command and output as a message to the agent
                    self.process_input(context_message)
                    self.set_mode(CLIMode.NORMAL)
                    continue

                # Process normal input
                self.process_input(user_input)

            except KeyboardInterrupt:
                # If Ctrl+C was pressed with empty buffer, we'll get here
                display_exit("Interrupted")
                break
            except EOFError:
                display_exit("Received EOF")
                break
            except Exception as e:
                display_error("Unexpected error", e)

    # Keep the run method as an alias for backwards compatibility
    def run(self) -> None:
        """Run the interactive prompt loop."""
        return self.run_interactive_loop()
