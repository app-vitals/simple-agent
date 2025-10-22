"""Tests for context extractor."""

from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from simple_agent.context.extractor import ContextExtractor
from simple_agent.context.manager import ContextManager
from simple_agent.context.schema import ContextType


@pytest.fixture
def temp_storage(tmp_path: Path) -> Path:
    """Create a temporary storage path for testing."""
    return tmp_path / "context.json"


@pytest.fixture
def mock_llm_client() -> Mock:
    """Create a mock LLM client."""
    mock = Mock()
    # Mock a successful response with tool call
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.tool_calls = [Mock()]
    mock_response.choices[0].message.tool_calls[
        0
    ].function.arguments = '{"facts": ["Test fact 1", "Test fact 2"]}'
    mock.send_completion.return_value = mock_response
    return mock


@pytest.fixture
def extractor(mock_llm_client: Mock, temp_storage: Path) -> ContextExtractor:
    """Create a context extractor with mocked LLM client."""
    extractor = ContextExtractor(llm_client=mock_llm_client)
    # Override context manager to use temp storage
    extractor.context_manager = ContextManager(storage_path=temp_storage)
    return extractor


def test_extract_and_store_with_user_message(
    extractor: ContextExtractor, mock_llm_client: Mock
) -> None:
    """Test extracting context from a user message."""
    facts = extractor.extract_and_store(
        user_message="I need to fix the auth bug for Acme Corp"
    )

    assert len(facts) == 2
    assert "Test fact 1" in facts
    assert "Test fact 2" in facts

    # Verify LLM was called
    assert mock_llm_client.send_completion.called

    # Verify facts were stored
    entries = extractor.context_manager.get_context()
    assert len(entries) == 2


def test_extract_and_store_with_tool_calls(
    extractor: ContextExtractor, mock_llm_client: Mock
) -> None:
    """Test extracting context from tool calls."""
    tool_calls = [
        {"name": "read_files", "arguments": {"file_paths": ["test.py"]}},
        {"name": "write_file", "arguments": {"file_path": "output.py"}},
    ]

    facts = extractor.extract_and_store(tool_calls=tool_calls)

    assert len(facts) == 2
    assert mock_llm_client.send_completion.called


def test_extract_and_store_empty_response(
    extractor: ContextExtractor, mock_llm_client: Mock
) -> None:
    """Test handling empty facts response."""
    mock_llm_client.send_completion.return_value.choices[0].message.tool_calls[
        0
    ].function.arguments = '{"facts": []}'

    facts = extractor.extract_and_store(user_message="Hello")

    assert len(facts) == 0
    assert mock_llm_client.send_completion.called


def test_extract_and_store_no_response(
    extractor: ContextExtractor, mock_llm_client: Mock
) -> None:
    """Test handling when LLM returns None."""
    mock_llm_client.send_completion.return_value = None

    facts = extractor.extract_and_store(user_message="Test")

    assert len(facts) == 0


def test_extract_and_store_no_input(extractor: ContextExtractor) -> None:
    """Test that extraction is skipped when no input provided."""
    facts = extractor.extract_and_store()

    assert len(facts) == 0


def test_determine_context_type_file(extractor: ContextExtractor) -> None:
    """Test context type determination for file operations."""
    tool_calls = [{"name": "read_files", "arguments": {}}]

    context_type = extractor._determine_context_type("Reading file.py", tool_calls)

    assert context_type == ContextType.FILE


def test_determine_context_type_calendar(extractor: ContextExtractor) -> None:
    """Test context type determination for calendar-related facts."""
    fact = "Has standup at 2pm"

    context_type = extractor._determine_context_type(fact, None)

    assert context_type == ContextType.CALENDAR


def test_determine_context_type_task(extractor: ContextExtractor) -> None:
    """Test context type determination for task-related facts."""
    fact = "Working on PR #234"

    context_type = extractor._determine_context_type(fact, None)

    assert context_type == ContextType.TASK


def test_determine_context_type_manual_fallback(
    extractor: ContextExtractor,
) -> None:
    """Test context type falls back to MANUAL for unknown types."""
    fact = "Some random fact"

    context_type = extractor._determine_context_type(fact, None)

    assert context_type == ContextType.MANUAL


def test_extract_from_messages(
    extractor: ContextExtractor, mock_llm_client: Mock
) -> None:
    """Test extracting context from a list of messages."""
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "Fix the bug"},
        {
            "role": "assistant",
            "content": "I'll help",
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {
                        "name": "read_files",
                        "arguments": '{"file_paths": ["bug.py"]}',
                    },
                }
            ],
        },
    ]

    facts = extractor.extract_from_messages(messages)

    assert len(facts) == 2
    assert mock_llm_client.send_completion.called


def test_extract_from_messages_dict_format(
    extractor: ContextExtractor, mock_llm_client: Mock
) -> None:
    """Test extracting context from messages in dict format."""
    messages: list[dict[str, Any]] = [
        {"role": "user", "content": "Test message"},
        {
            "role": "assistant",
            "tool_calls": [
                {
                    "function": {
                        "name": "write_file",
                        "arguments": '{"file_path": "test.py"}',
                    }
                }
            ],
        },
    ]

    facts = extractor.extract_from_messages(messages)

    assert len(facts) == 2


def test_get_recent_context_summary(
    extractor: ContextExtractor, temp_storage: Path
) -> None:
    """Test getting formatted context summary."""
    # Add some context
    extractor.context_manager.add_context(
        type=ContextType.TASK, source="test", content="Working on feature X"
    )
    extractor.context_manager.add_context(
        type=ContextType.FILE, source="test", content="Edited file.py"
    )

    summary = extractor.get_recent_context_summary()

    assert "Recent Context:" in summary
    assert "Task:" in summary
    assert "Working on feature X" in summary
    assert "File:" in summary
    assert "Edited file.py" in summary


def test_get_recent_context_summary_empty(extractor: ContextExtractor) -> None:
    """Test context summary when no context available."""
    summary = extractor.get_recent_context_summary()

    assert "No recent context available" in summary


def test_context_metadata_stored(
    extractor: ContextExtractor, mock_llm_client: Mock
) -> None:
    """Test that metadata is stored with extracted facts."""
    user_message = "This is a test message that is quite long"

    extractor.extract_and_store(user_message=user_message)

    entries = extractor.context_manager.get_context()
    assert len(entries) == 2

    # Check metadata
    for entry in entries:
        assert entry.metadata["extraction_method"] == "llm"
        assert "user_message" in entry.metadata
        # User message should be truncated to 100 chars
        assert len(entry.metadata["user_message"]) <= 100
