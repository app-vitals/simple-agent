"""Command and completion functionality for the CLI."""

from collections.abc import Iterable

from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document


class CommandCompleter(Completer):
    """Command completer for Simple Agent."""

    def __init__(self) -> None:
        """Initialize command completer."""
        # Define commands with descriptions
        self.commands = {
            "/help": "Show help information",
            "/exit": "Exit the application",
            "/clear": "Clear the screen",
            "\\ + Enter": "to create a new line",
        }

    def get_completions(
        self, document: Document, complete_event: CompleteEvent
    ) -> Iterable[Completion]:
        """Get completions for the current document."""
        word = document.get_word_before_cursor()
        text_before_cursor = document.text_before_cursor

        # Only show slash commands if we're at the beginning of the line
        # or if we've just typed a slash as the first character
        is_first_position = (
            not text_before_cursor.strip() or text_before_cursor.strip() == "/"
        )

        for command, description in self.commands.items():
            # Only suggest slash commands if they're appropriate for the position
            if command.startswith("/") and not is_first_position:
                continue

            if command.startswith(word):
                yield Completion(
                    command,
                    start_position=-len(word),
                    display=command,
                    display_meta=description,
                )
