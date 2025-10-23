"""Tests for message manager."""

from pathlib import Path

import pytest

from simple_agent.messages.manager import MessageManager


@pytest.fixture
def temp_storage_path(tmp_path: Path) -> Path:
    """Create a temporary storage path for testing."""
    return tmp_path / ".simple-agent" / "messages.json"


@pytest.fixture
def manager(temp_storage_path: Path) -> MessageManager:
    """Create a message manager with temporary storage."""
    mgr = MessageManager(max_messages=5)
    mgr.storage.storage_path = temp_storage_path
    mgr.storage._ensure_storage_exists()
    return mgr


def test_manager_init(manager: MessageManager) -> None:
    """Test manager initialization."""
    assert len(manager) == 0
    assert manager.storage.max_messages == 5


def test_append_message(manager: MessageManager) -> None:
    """Test appending a message."""
    manager.append({"role": "user", "content": "Hello"})

    assert len(manager) == 1
    assert manager[0]["role"] == "user"
    assert manager[0]["content"] == "Hello"


def test_append_auto_saves(manager: MessageManager, temp_storage_path: Path) -> None:
    """Test that append automatically saves to disk."""
    manager.append({"role": "user", "content": "Hello"})

    # Create new manager and load
    new_manager = MessageManager(max_messages=5)
    new_manager.storage.storage_path = temp_storage_path
    new_manager.load()

    assert len(new_manager) == 1
    assert new_manager[0]["content"] == "Hello"


def test_extend_messages(manager: MessageManager) -> None:
    """Test extending messages list."""
    messages = [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Second"},
    ]

    manager.extend(messages)

    assert len(manager) == 2
    assert manager[0]["content"] == "First"
    assert manager[1]["content"] == "Second"


def test_extend_auto_saves(manager: MessageManager, temp_storage_path: Path) -> None:
    """Test that extend automatically saves to disk."""
    messages = [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Second"},
    ]

    manager.extend(messages)

    # Create new manager and load
    new_manager = MessageManager(max_messages=5)
    new_manager.storage.storage_path = temp_storage_path
    new_manager.load()

    assert len(new_manager) == 2


def test_update_last(manager: MessageManager) -> None:
    """Test updating the last message."""
    manager.append({"role": "user", "content": "First"})
    manager.append({"role": "user", "content": "Second"})

    manager.update_last({"role": "user", "content": "Updated"})

    assert len(manager) == 2
    assert manager[-1]["content"] == "Updated"


def test_update_at_index(manager: MessageManager) -> None:
    """Test updating a message at specific index."""
    manager.append({"role": "user", "content": "First"})
    manager.append({"role": "user", "content": "Second"})

    manager.update_at_index(0, {"role": "user", "content": "Updated"})

    assert manager[0]["content"] == "Updated"
    assert manager[1]["content"] == "Second"


def test_get_all(manager: MessageManager) -> None:
    """Test getting all messages."""
    messages = [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Second"},
    ]

    manager.extend(messages)
    all_messages = manager.get_all()

    assert all_messages == messages


def test_build_for_llm(manager: MessageManager) -> None:
    """Test building message list for LLM with system prompt."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
    ]

    manager.extend(messages)
    llm_messages = manager.build_for_llm("You are a helpful assistant")

    assert len(llm_messages) == 3
    assert llm_messages[0]["role"] == "system"
    assert llm_messages[0]["content"] == "You are a helpful assistant"
    assert llm_messages[1]["role"] == "user"
    assert llm_messages[2]["role"] == "assistant"


def test_build_for_llm_empty(manager: MessageManager) -> None:
    """Test building for LLM with no messages."""
    llm_messages = manager.build_for_llm("System prompt")

    assert len(llm_messages) == 1
    assert llm_messages[0]["role"] == "system"


def test_clear(manager: MessageManager, temp_storage_path: Path) -> None:
    """Test clearing messages."""
    manager.append({"role": "user", "content": "Hello"})
    assert len(manager) == 1

    manager.clear()
    assert len(manager) == 0

    # Verify disk is also cleared
    new_manager = MessageManager(max_messages=5)
    new_manager.storage.storage_path = temp_storage_path
    new_manager.load()
    assert len(new_manager) == 0


def test_len(manager: MessageManager) -> None:
    """Test length operator."""
    assert len(manager) == 0

    manager.append({"role": "user", "content": "Hello"})
    assert len(manager) == 1

    manager.append({"role": "assistant", "content": "Hi"})
    assert len(manager) == 2


def test_getitem(manager: MessageManager) -> None:
    """Test indexing operator."""
    manager.append({"role": "user", "content": "First"})
    manager.append({"role": "user", "content": "Second"})

    assert manager[0]["content"] == "First"
    assert manager[1]["content"] == "Second"
    assert manager[-1]["content"] == "Second"


def test_setitem(manager: MessageManager, temp_storage_path: Path) -> None:
    """Test setting item by index."""
    manager.append({"role": "user", "content": "First"})

    manager[0] = {"role": "user", "content": "Updated"}

    assert manager[0]["content"] == "Updated"

    # Verify it saved
    new_manager = MessageManager(max_messages=5)
    new_manager.storage.storage_path = temp_storage_path
    new_manager.load()
    assert new_manager[0]["content"] == "Updated"


def test_load_preserves_order(manager: MessageManager, temp_storage_path: Path) -> None:
    """Test that loading preserves message order."""
    messages = [
        {"role": "user", "content": "First"},
        {"role": "assistant", "content": "Second"},
        {"role": "user", "content": "Third"},
    ]

    manager.extend(messages)

    new_manager = MessageManager(max_messages=5)
    new_manager.storage.storage_path = temp_storage_path
    new_manager.load()

    for i, msg in enumerate(messages):
        assert new_manager[i] == msg


def test_max_messages_limit(manager: MessageManager, temp_storage_path: Path) -> None:
    """Test that max_messages limit is enforced on save."""
    # Add 10 messages
    for i in range(10):
        manager.append({"role": "user", "content": f"Message {i}"})

    # Load in new manager - should only have last 5
    new_manager = MessageManager(max_messages=5)
    new_manager.storage.storage_path = temp_storage_path
    new_manager.load()

    assert len(new_manager) == 5
    assert new_manager[0]["content"] == "Message 5"
    assert new_manager[-1]["content"] == "Message 9"
