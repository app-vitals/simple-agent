"""Context manager for storing and retrieving context entries."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from simple_agent.context.schema import ContextEntry, ContextStore, ContextType


class ContextManager:
    """Manages context entries with disk-based persistence."""

    def __init__(
        self,
        storage_path: Path | None = None,
        max_age_days: int = 7,
    ) -> None:
        """Initialize the context manager.

        Args:
            storage_path: Path to context.json file. Defaults to ~/.simple-agent/context.json
            max_age_days: Maximum age of context entries in days before auto-cleanup
        """
        if storage_path is None:
            storage_path = Path.home() / ".simple-agent" / "context.json"

        self.storage_path = storage_path
        self.max_age_days = max_age_days
        self._ensure_storage_dir()

    def _ensure_storage_dir(self) -> None:
        """Ensure the storage directory exists."""
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_store(self) -> ContextStore:
        """Load context store from disk."""
        if not self.storage_path.exists():
            return ContextStore()

        try:
            with open(self.storage_path) as f:
                data = json.load(f)
                return ContextStore.model_validate(data)
        except (json.JSONDecodeError, ValueError) as e:
            # If file is corrupted, start fresh but log the error
            print(f"Warning: Could not load context from {self.storage_path}: {e}")
            return ContextStore()

    def _save_store(self, store: ContextStore) -> None:
        """Save context store to disk."""
        with open(self.storage_path, "w") as f:
            json.dump(store.model_dump(), f, indent=2, default=str)

    def _cleanup_old_entries(self, store: ContextStore) -> ContextStore:
        """Remove entries older than max_age_days."""
        cutoff = datetime.now() - timedelta(days=self.max_age_days)
        store.entries = [e for e in store.entries if e.timestamp >= cutoff]
        return store

    def add_context(
        self,
        type: ContextType,
        source: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> ContextEntry:
        """Add a new context entry.

        Args:
            type: Type of context entry
            source: Source of the context (e.g., "user", "toggl", "google_calendar")
            content: Human-readable description of the context
            metadata: Optional additional metadata

        Returns:
            The created ContextEntry
        """
        entry = ContextEntry(
            type=type,
            source=source,
            content=content,
            metadata=metadata or {},
        )

        store = self._load_store()
        store.entries.append(entry)
        self._save_store(store)

        return entry

    def get_context(
        self,
        type: ContextType | None = None,
        max_age_hours: int | None = None,
        limit: int | None = None,
    ) -> list[ContextEntry]:
        """Retrieve context entries with optional filtering.

        Args:
            type: Filter by context type (optional)
            max_age_hours: Only return entries newer than this many hours (optional)
            limit: Maximum number of entries to return (optional)

        Returns:
            List of matching context entries, sorted by timestamp (newest first)
        """
        store = self._load_store()
        store = self._cleanup_old_entries(store)
        self._save_store(store)  # Save after cleanup

        entries = store.entries

        # Filter by type if specified
        if type is not None:
            entries = [e for e in entries if e.type == type]

        # Filter by age if specified
        if max_age_hours is not None:
            cutoff = datetime.now() - timedelta(hours=max_age_hours)
            entries = [e for e in entries if e.timestamp >= cutoff]

        # Sort by timestamp (newest first)
        entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)

        # Limit results if specified
        if limit is not None:
            entries = entries[:limit]

        return entries

    def clear_context(self, type: ContextType | None = None) -> int:
        """Clear context entries.

        Args:
            type: Only clear entries of this type (optional). If None, clears all.

        Returns:
            Number of entries cleared
        """
        store = self._load_store()
        initial_count = len(store.entries)

        if type is None:
            # Clear all entries
            store.entries = []
        else:
            # Clear only entries of specified type
            store.entries = [e for e in store.entries if e.type != type]

        self._save_store(store)
        return initial_count - len(store.entries)

    def get_context_summary(self) -> dict[str, Any]:
        """Get a summary of current context.

        Returns:
            Dictionary with context statistics
        """
        entries = self.get_context()

        # Count by type
        type_counts: dict[str, int] = {}
        for entry in entries:
            type_counts[entry.type.value] = type_counts.get(entry.type.value, 0) + 1

        # Get oldest and newest
        oldest = min((e.timestamp for e in entries), default=None)
        newest = max((e.timestamp for e in entries), default=None)

        return {
            "total_entries": len(entries),
            "by_type": type_counts,
            "oldest_entry": oldest.isoformat() if oldest else None,
            "newest_entry": newest.isoformat() if newest else None,
        }
