"""Prompt Toolkit interface for Simple Agent."""

import os
from collections.abc import Callable
from enum import Enum
from typing import Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys
from prompt_toolkit.shortcuts import clear
from prompt_toolkit.styles import Style
from rich.padding import Padding

from simple_agent.cli.completion import Completer
from simple_agent.config import config
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
[bold]Simple Agent[/bold] - Your execution efficiency assistant

Help you execute on short-term tasks and long-term goals.

[bold]How I help:[/bold]
• Answer "what should I work on next?" based on your context
• Remember your projects, files, and working patterns
• Track progress toward long-term goals
• Suggest high-priority actions that fit your available time

[bold]Commands:[/bold]
• [green]/help[/green]:          Show this help message
• [green]/clear[/green]:         Clear the terminal screen and conversation history
• [green]/compress[/green]:      Compress conversation to context files
• [green]/mcp[/green]:           View configured MCP servers
• [green]/exit[/green]:          Exit the agent
• [green]![/green]:              Run a shell command directly

[bold]Input features:[/bold]
• End a line with [green]\\ [/green]for aligned multi-line input
• Use Tab key for command auto-completion

Just ask me what to work on next, and I'll help you prioritize.
"""


class CLI:
    """Interactive CLI for Simple Agent."""

    def __init__(
        self,
        process_input_callback: Callable[[str], None],
        on_start_callback: Callable[[], None] | None = None,
        message_manager: Any | None = None,
        mcp_manager: Any | None = None,
        mcp_errors: dict[str, str] | None = None,
    ) -> None:
        """Initialize the CLI.

        Args:
            process_input_callback: Callback for processing user input
            on_start_callback: Optional callback to run after splash screen
            message_manager: Optional message manager for clearing conversation history
            mcp_manager: Optional MCP manager for displaying server status
            mcp_errors: Optional dictionary of MCP server load errors
        """
        self.process_input = process_input_callback
        self.on_start_callback = on_start_callback
        self.message_manager = message_manager
        self.mcp_manager = mcp_manager
        self.mcp_errors = mcp_errors or {}
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
        console.print(Padding(HELP_TEXT, (0, 0, 0, 2)))

    def show_mcp_servers(self) -> None:
        """Display configured MCP servers and their status."""
        if not config.mcp_servers:
            console.print()
            console.print(
                Padding("[dim]No MCP servers configured.[/dim]", (0, 0, 0, 2))
            )
            console.print()
            return

        if config.mcp_disabled:
            console.print()
            console.print(
                Padding(
                    "[yellow]MCP servers are disabled (SIMPLE_AGENT_DISABLE_MCP=true)[/yellow]",
                    (0, 0, 0, 2),
                )
            )
            console.print()

        console.print()
        console.print(
            Padding("[bold cyan]Configured MCP Servers:[/bold cyan]", (0, 0, 0, 2))
        )

        for server_name in config.mcp_servers:
            # Check if server is running or has errors
            if server_name in self.mcp_errors:
                status = "[red]failed to load[/red]"
            elif self.mcp_manager and server_name in self.mcp_manager.sessions:
                status = "[green]running[/green]"
            else:
                status = "[red]not running[/red]"

            console.print(Padding(f"{server_name} - {status}", (0, 0, 0, 2)))

        console.print()

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
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃          🤖 Simple Agent                      ┃
┃                                                ┃
┃ /help           for available commands         ┃
┃ /clear          clear screen & conversation    ┃
┃ /compress       compress to context files      ┃
┃ /mcp            view MCP servers               ┃
┃ /exit           to quit                        ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
"""
        # Using direct console.print since we want custom formatting for the welcome box
        console.print(
            Padding(f"[bold white]{welcome_message}[/bold white]", (0, 0, 0, 2))
        )

        # Call on_start_callback after splash screen (if provided)
        if self.on_start_callback:
            self.on_start_callback()

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
                    # Also clear message history if message manager is available
                    if self.message_manager:
                        self.message_manager.clear()
                        console.print(
                            Padding(
                                "[green]Conversation history cleared.[/green]",
                                (0, 0, 0, 2),
                            )
                        )
                    continue
                elif user_input.lower().startswith("/compress"):
                    # Extract optional instructions after /compress
                    parts = user_input.split(maxsplit=1)
                    instructions = parts[1] if len(parts) > 1 else ""
                    # Pass to process_input with special marker
                    self.process_input(f"__COMPRESS__{instructions}")
                    continue
                elif user_input.lower() == "/mcp":
                    self.show_mcp_servers()
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
