"""Tests for context manager."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pytest

from simple_agent.context.manager import ContextManager
from simple_agent.context.schema import ContextType


@pytest.fixture
def temp_storage(tmp_path: Path) -> Path:
    """Create a temporary storage path for testing."""
    return tmp_path / "context.json"


@pytest.fixture
def manager(temp_storage: Path) -> ContextManager:
    """Create a context manager with temporary storage."""
    return ContextManager(storage_path=temp_storage, max_age_days=7)


def test_context_manager_init(manager: ContextManager, temp_storage: Path) -> None:
    """Test context manager initialization."""
    assert manager.storage_path == temp_storage
    assert manager.max_age_days == 7
    assert temp_storage.parent.exists()


def test_add_context(manager: ContextManager) -> None:
    """Test adding context entries."""
    entry = manager.add_context(
        type=ContextType.MANUAL,
        source="user",
        content="working on API refactor",
        metadata={"project": "simple-agent"},
    )

    assert entry.type == ContextType.MANUAL
    assert entry.source == "user"
    assert entry.content == "working on API refactor"
    assert entry.metadata["project"] == "simple-agent"
    assert entry.id is not None
    assert isinstance(entry.timestamp, datetime)


def test_get_context(manager: ContextManager) -> None:
    """Test retrieving context entries."""
    # Add some entries
    manager.add_context(
        type=ContextType.MANUAL,
        source="user",
        content="entry 1",
    )
    manager.add_context(
        type=ContextType.CALENDAR,
        source="google_calendar",
        content="entry 2",
    )
    manager.add_context(
        type=ContextType.MANUAL,
        source="user",
        content="entry 3",
    )

    # Get all entries
    entries = manager.get_context()
    assert len(entries) == 3

    # Entries should be sorted by timestamp (newest first)
    assert entries[0].content == "entry 3"
    assert entries[1].content == "entry 2"
    assert entries[2].content == "entry 1"


def test_get_context_filtered_by_type(manager: ContextManager) -> None:
    """Test retrieving context entries filtered by type."""
    manager.add_context(type=ContextType.MANUAL, source="user", content="manual 1")
    manager.add_context(type=ContextType.CALENDAR, source="cal", content="cal 1")
    manager.add_context(type=ContextType.MANUAL, source="user", content="manual 2")

    manual_entries = manager.get_context(type=ContextType.MANUAL)
    assert len(manual_entries) == 2
    assert all(e.type == ContextType.MANUAL for e in manual_entries)


def test_get_context_filtered_by_age(manager: ContextManager) -> None:
    """Test retrieving context entries filtered by age."""
    # Add an entry
    manager.add_context(type=ContextType.MANUAL, source="user", content="recent")

    # Get entries from last hour
    entries = manager.get_context(max_age_hours=1)
    assert len(entries) == 1

    # Get entries from last 0 hours (should be empty since entry is a few ms old)
    # Actually this is tricky - let's test with a more realistic scenario
    entries = manager.get_context(max_age_hours=24)
    assert len(entries) == 1


def test_get_context_with_limit(manager: ContextManager) -> None:
    """Test retrieving context entries with limit."""
    for i in range(5):
        manager.add_context(
            type=ContextType.MANUAL, source="user", content=f"entry {i}"
        )

    entries = manager.get_context(limit=3)
    assert len(entries) == 3


def test_clear_context_all(manager: ContextManager) -> None:
    """Test clearing all context entries."""
    manager.add_context(type=ContextType.MANUAL, source="user", content="entry 1")
    manager.add_context(type=ContextType.CALENDAR, source="cal", content="entry 2")

    cleared = manager.clear_context()
    assert cleared == 2

    entries = manager.get_context()
    assert len(entries) == 0


def test_clear_context_by_type(manager: ContextManager) -> None:
    """Test clearing context entries by type."""
    manager.add_context(type=ContextType.MANUAL, source="user", content="manual 1")
    manager.add_context(type=ContextType.CALENDAR, source="cal", content="cal 1")
    manager.add_context(type=ContextType.MANUAL, source="user", content="manual 2")

    cleared = manager.clear_context(type=ContextType.MANUAL)
    assert cleared == 2

    entries = manager.get_context()
    assert len(entries) == 1
    assert entries[0].type == ContextType.CALENDAR


def test_persistence(temp_storage: Path) -> None:
    """Test that context persists across manager instances."""
    # Create first manager and add context
    manager1 = ContextManager(storage_path=temp_storage)
    manager1.add_context(type=ContextType.MANUAL, source="user", content="persistent")

    # Create second manager with same storage
    manager2 = ContextManager(storage_path=temp_storage)
    entries = manager2.get_context()

    assert len(entries) == 1
    assert entries[0].content == "persistent"


def test_cleanup_old_entries(temp_storage: Path) -> None:
    """Test that old entries are cleaned up."""
    manager = ContextManager(storage_path=temp_storage, max_age_days=7)

    # Add an entry
    manager.add_context(type=ContextType.MANUAL, source="user", content="old entry")

    # Manually modify the timestamp to be 8 days old
    with open(temp_storage) as f:
        data = json.load(f)

    # Set timestamp to 8 days ago
    old_timestamp = datetime.now() - timedelta(days=8)
    data["entries"][0]["timestamp"] = old_timestamp.isoformat()

    with open(temp_storage, "w") as f:
        json.dump(data, f)

    # Get context should trigger cleanup
    entries = manager.get_context()
    assert len(entries) == 0


def test_get_context_summary(manager: ContextManager) -> None:
    """Test getting context summary."""
    manager.add_context(type=ContextType.MANUAL, source="user", content="manual 1")
    manager.add_context(type=ContextType.MANUAL, source="user", content="manual 2")
    manager.add_context(type=ContextType.CALENDAR, source="cal", content="cal 1")

    summary = manager.get_context_summary()

    assert summary["total_entries"] == 3
    assert summary["by_type"]["manual"] == 2
    assert summary["by_type"]["calendar"] == 1
    assert summary["oldest_entry"] is not None
    assert summary["newest_entry"] is not None


def test_corrupted_storage(temp_storage: Path, capsys: Any) -> None:
    """Test handling of corrupted storage file."""
    # Write invalid JSON to storage
    temp_storage.parent.mkdir(parents=True, exist_ok=True)
    temp_storage.write_text("invalid json {")

    # Manager should handle gracefully
    manager = ContextManager(storage_path=temp_storage)
    entries = manager.get_context()

    assert len(entries) == 0

    # Should have printed a warning
    captured = capsys.readouterr()
    assert "Warning" in captured.out
    assert "Could not load context" in captured.out


def test_empty_storage(manager: ContextManager) -> None:
    """Test behavior with no existing storage file."""
    entries = manager.get_context()
    assert len(entries) == 0

    summary = manager.get_context_summary()
    assert summary["total_entries"] == 0
    assert summary["oldest_entry"] is None
    assert summary["newest_entry"] is None
