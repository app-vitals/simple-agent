"""Tests for message storage."""

from pathlib import Path

import pytest

from simple_agent.messages.storage import MessageStorage


@pytest.fixture
def temp_storage_path(tmp_path: Path) -> Path:
    """Create a temporary storage path for testing."""
    return tmp_path / ".simple-agent" / "messages.json"


@pytest.fixture
def storage(temp_storage_path: Path) -> MessageStorage:
    """Create a message storage with temporary path."""
    storage = MessageStorage(max_messages=5)
    storage.storage_path = temp_storage_path
    storage._ensure_storage_exists()
    return storage


def test_storage_init(storage: MessageStorage, temp_storage_path: Path) -> None:
    """Test storage initialization."""
    assert storage.storage_path == temp_storage_path
    assert storage.max_messages == 5
    assert temp_storage_path.exists()


def test_save_and_load_messages(storage: MessageStorage) -> None:
    """Test saving and loading messages."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    storage.save_messages(messages)
    loaded = storage.load_messages()

    assert loaded == messages


def test_save_excludes_system_messages(storage: MessageStorage) -> None:
    """Test that system messages are excluded from storage."""
    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]

    storage.save_messages(messages)
    loaded = storage.load_messages()

    # System message should be filtered out
    assert len(loaded) == 2
    assert loaded[0]["role"] == "user"
    assert loaded[1]["role"] == "assistant"


def test_save_respects_max_messages(storage: MessageStorage) -> None:
    """Test that max_messages limit is enforced."""
    messages = [{"role": "user", "content": f"Message {i}"} for i in range(10)]

    storage.save_messages(messages)
    loaded = storage.load_messages()

    # Should only keep last 5 messages
    assert len(loaded) == 5
    assert loaded[0]["content"] == "Message 5"
    assert loaded[-1]["content"] == "Message 9"


def test_save_empty_messages(storage: MessageStorage) -> None:
    """Test saving empty message list."""
    storage.save_messages([])
    loaded = storage.load_messages()

    assert loaded == []


def test_load_nonexistent_file(tmp_path: Path) -> None:
    """Test loading from nonexistent file."""
    storage = MessageStorage(max_messages=5)
    storage.storage_path = tmp_path / "nonexistent.json"

    loaded = storage.load_messages()
    assert loaded == []


def test_load_corrupted_file(storage: MessageStorage) -> None:
    """Test loading from corrupted JSON file."""
    # Write invalid JSON
    storage.storage_path.write_text("invalid json {{{")

    # Should return empty list and display warning
    loaded = storage.load_messages()
    assert loaded == []


def test_load_invalid_format(storage: MessageStorage) -> None:
    """Test loading file with invalid format (not a list)."""
    # Write valid JSON but not a list
    storage.storage_path.write_text('{"invalid": "format"}')

    loaded = storage.load_messages()
    assert loaded == []


def test_clear_messages(storage: MessageStorage) -> None:
    """Test clearing messages."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]

    storage.save_messages(messages)
    assert len(storage.load_messages()) == 2

    storage.clear_messages()
    assert storage.load_messages() == []


def test_multiple_save_operations(storage: MessageStorage) -> None:
    """Test multiple save operations overwrite correctly."""
    messages1 = [{"role": "user", "content": "First"}]
    messages2 = [
        {"role": "user", "content": "Second"},
        {"role": "assistant", "content": "Response"},
    ]

    storage.save_messages(messages1)
    loaded1 = storage.load_messages()
    assert len(loaded1) == 1

    storage.save_messages(messages2)
    loaded2 = storage.load_messages()
    assert len(loaded2) == 2
    assert loaded2[0]["content"] == "Second"
