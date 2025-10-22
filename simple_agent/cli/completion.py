"""Command and completion functionality for the CLI."""

from collections.abc import Iterable

from prompt_toolkit.completion import (
    CompleteEvent,
    Completion,
    PathCompleter,
)
from prompt_toolkit.completion import (
    Completer as PTKCompleter,
)
from prompt_toolkit.document import Document


class CommandCompleter(PTKCompleter):
    """Command completer for Simple Agent."""

    def __init__(self) -> None:
        """Initialize command completer."""
        # Define commands with descriptions
        self.commands = {
            "/help": "Show help information",
            "/exit": "Exit the application",
            "/clear": "Clear the screen",
            "/show-context": "Show recent context entries",
            "/clear-context": "Clear all context entries",
            "\\ + Enter": "to create a new line",
        }

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get completions for the current document."""
        text_before_cursor = document.text_before_cursor.strip()

        # Only show slash commands if we're at the beginning of the line
        # and the text starts with /
        if not text_before_cursor.startswith("/"):
            return

        for command, description in self.commands.items():
            # Skip non-slash commands
            if not command.startswith("/"):
                continue

            if command.startswith(text_before_cursor):
                yield Completion(
                    command,
                    start_position=-len(text_before_cursor),
                    display=command,
                    display_meta=description,
                )


class FilePathCompleter(PTKCompleter):
    """File path completer for Simple Agent.

    Wraps prompt_toolkit's PathCompleter with additional functionality.
    """

    def __init__(self) -> None:
        """Initialize file path completer."""
        self.path_completer = PathCompleter(
            expanduser=True,
            only_directories=False,
            file_filter=None,
            min_input_len=1,
        )

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get file path completions for the current document."""
        text = document.text_before_cursor
        # Get the last word (after any spaces) to handle file paths in commands
        text = text.split(" ")[-1]
        sub_document = Document(text)

        # Only activate for file paths (not commands starting with /)
        # Trigger on: ./, ~/, or absolute paths like /usr/local
        # Don't trigger on single / at start of line (that's for commands)
        is_file_path = (
            text.startswith("./")
            or text.startswith("~/")
            or (
                text.startswith("/") and "/" in text[1:]
            )  # /path/to/file but not just /
        )

        if is_file_path:
            yield from self.path_completer.get_completions(sub_document, complete_event)


class Completer(PTKCompleter):
    """Completer for Simple Agent that provides both command and file path completions."""

    def __init__(self) -> None:
        """Initialize with command and file completers."""
        self.command_completer = CommandCompleter()
        self.file_completer = FilePathCompleter()

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get completions from all underlying completers."""
        # Try command completions first
        cmd_completions = list(
            self.command_completer.get_completions(document, complete_event)
        )
        if cmd_completions:
            yield from cmd_completions
            return

        # If no command completions, try file completions
        yield from self.file_completer.get_completions(document, complete_event)
