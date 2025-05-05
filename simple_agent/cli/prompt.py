"""Prompt Toolkit interface for Simple Agent."""

import os
import subprocess
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
from simple_agent.display import (
    console,
    display_command,
    display_command_output,
    display_error,
    display_info,
    display_warning,
)


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
• [green]![/green]:      Run a shell command

[bold]Input features:[/bold]
• End a line with [green]\\ [/green]for aligned multi-line input
• Use Tab key for command auto-completion

[bold]Response types:[/bold]
• [blue]Next action[/blue]: The agent knows what to do next and will continue automatically
• [yellow]Question[/yellow]: The agent needs more information from you
• Normal response: The task is complete
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

    def execute_command(self, command: str) -> str:
        """Execute a bash command and return the output.

        Args:
            command: The command to execute

        Returns:
            The command output (stdout and stderr)
        """
        try:
            # Run the command using the shell
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                check=False,
            )

            # Combine stdout and stderr for display
            output = result.stdout
            if result.stderr:
                if output:
                    output += "\n" + result.stderr
                else:
                    output = result.stderr

            return output
        except Exception as e:
            return f"Error executing command: {e}"

    def run_interactive_loop(self) -> None:
        """Run the interactive prompt loop."""
        # Display welcome message with styling
        welcome_message = """
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          🤖 Simple Agent           ┃
┃                                    ┃
┃ /help      for available commands  ┃
┃ /clear     to clear the screen     ┃
┃ /exit      to quit                 ┃
┃ !          to run a shell command  ┃
┃ \\ + Enter  to create a newline     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
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
                    display_info("Goodbye! Exiting Simple Agent.")
                    break
                elif user_input.lower() == "/help":
                    self.show_help()
                    continue
                elif user_input.lower() == "/clear":
                    clear()
                    continue
                elif user_input.startswith("/"):
                    # Handle unknown slash commands
                    display_warning(f"Unknown command: {user_input}")
                    continue

                if self.mode == CLIMode.SHELL:
                    # Print the command being executed
                    display_command(user_input)

                    # Execute the command
                    output = self.execute_command(user_input)

                    # Display the output
                    if output:
                        display_command_output(output)

                    # Format combined input for the agent context
                    context_message = f"Command:\n```bash\n$ {user_input}\n```\nOutput:\n```\n{output}\n```"

                    # Process the command and output as a message to the agent
                    self.process_input(context_message)
                    self.set_mode(CLIMode.NORMAL)
                    continue

                # Process normal input
                self.process_input(user_input)

            except KeyboardInterrupt:
                # If Ctrl+C was pressed with empty buffer, we'll get here
                display_warning("\nInterrupted. Exiting.")
                break
            except EOFError:
                display_warning("\nReceived EOF. Exiting.")
                break
            except Exception as e:
                display_error("Unexpected error", e)

    # Keep the run method as an alias for backwards compatibility
    def run(self) -> None:
        """Run the interactive prompt loop."""
        return self.run_interactive_loop()
