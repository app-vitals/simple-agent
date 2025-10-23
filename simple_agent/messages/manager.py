"""Message manager for conversation history with automatic persistence."""

from typing import Any

from simple_agent.messages.storage import MessageStorage


class MessageManager:
    """Manages conversation messages with automatic persistence to disk."""

    def __init__(self, max_messages: int = 50):
        """Initialize message manager.

        Args:
            max_messages: Maximum number of messages to store (default: 50)
        """
        self.storage = MessageStorage(max_messages=max_messages)
        self._messages: list[dict[str, Any]] = []

    def load(self) -> None:
        """Load messages from disk."""
        self._messages = self.storage.load_messages()

    def append(self, message: dict[str, Any]) -> None:
        """Append a message and save to disk.

        Args:
            message: Message dictionary to append
        """
        self._messages.append(message)
        self.storage.save_messages(self._messages)

    def extend(self, messages: list[dict[str, Any]]) -> None:
        """Extend messages list and save to disk.

        Args:
            messages: List of message dictionaries to append
        """
        self._messages.extend(messages)
        self.storage.save_messages(self._messages)

    def update_last(self, message: dict[str, Any]) -> None:
        """Update the last message and save to disk.

        Args:
            message: Message dictionary to replace the last message with
        """
        if self._messages:
            self._messages[-1] = message
            self.storage.save_messages(self._messages)

    def update_at_index(self, index: int, message: dict[str, Any]) -> None:
        """Update a message at a specific index and save to disk.

        Args:
            index: Index of message to update
            message: Message dictionary to replace with
        """
        if 0 <= index < len(self._messages):
            self._messages[index] = message
            self.storage.save_messages(self._messages)

    def get_all(self) -> list[dict[str, Any]]:
        """Get all messages.

        Returns:
            List of all message dictionaries
        """
        return self._messages

    def build_for_llm(self, system_prompt: str) -> list[dict[str, Any]]:
        """Build message list for LLM with system prompt prepended.

        Args:
            system_prompt: The system prompt content to prepend

        Returns:
            List of messages with system prompt as first message
        """
        return [{"role": "system", "content": system_prompt}] + self._messages

    def clear(self) -> None:
        """Clear all messages and delete from disk."""
        self._messages = []
        self.storage.clear_messages()

    def __len__(self) -> int:
        """Get number of messages.

        Returns:
            Number of messages in the list
        """
        return len(self._messages)

    def __getitem__(self, index: int) -> dict[str, Any]:
        """Get message at index.

        Args:
            index: Index of message to retrieve

        Returns:
            Message dictionary at the specified index
        """
        return self._messages[index]

    def __setitem__(self, index: int, message: dict[str, Any]) -> None:
        """Set message at index and save to disk.

        Args:
            index: Index of message to update
            message: Message dictionary to set
        """
        self._messages[index] = message
        self.storage.save_messages(self._messages)
