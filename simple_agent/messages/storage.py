"""Message persistence for conversation history."""

import json
from pathlib import Path
from typing import Any

from simple_agent.display import display_warning


class MessageStorage:
    """Handles reading and writing conversation messages to disk."""

    def __init__(self, max_messages: int = 50):
        """Initialize message storage.

        Args:
            max_messages: Maximum number of messages to store (default: 50)
        """
        self.storage_path = Path.home() / ".simple-agent" / "messages.json"
        self.max_messages = max_messages
        self._ensure_storage_exists()

    def _ensure_storage_exists(self) -> None:
        """Ensure the storage directory and file exist."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self._write_messages([])

    def _write_messages(self, messages: list[dict[str, Any]]) -> None:
        """Write messages to disk."""
        with open(self.storage_path, "w") as f:
            json.dump(messages, f, indent=2, default=str)

    def save_messages(self, messages: list[dict[str, Any]]) -> None:
        """Save messages to disk, keeping only the most recent ones.

        System messages are excluded from storage as they are generated dynamically.
        Messages are limited to max_messages.

        Args:
            messages: List of message dictionaries to save
        """
        if not messages:
            self._write_messages([])
            return

        # Filter out system messages - they're generated dynamically
        conversation_messages = [msg for msg in messages if msg.get("role") != "system"]

        # Limit conversation messages to max_messages
        if len(conversation_messages) > self.max_messages:
            conversation_messages = conversation_messages[-self.max_messages :]

        self._write_messages(conversation_messages)

    def load_messages(self) -> list[dict[str, Any]]:
        """Load messages from disk.

        Returns:
            List of message dictionaries, or empty list if file doesn't exist
        """
        if not self.storage_path.exists():
            return []

        try:
            with open(self.storage_path) as f:
                messages = json.load(f)
                return messages if isinstance(messages, list) else []
        except Exception as e:
            # If file is corrupted or can't be read, show warning and return empty list
            display_warning(
                "Could not load messages.json, starting fresh conversation", e
            )
            return []

    def clear_messages(self) -> None:
        """Clear all stored messages."""
        self._write_messages([])
