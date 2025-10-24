"""Tests for compression prompt."""

from simple_agent.context.compression_prompt import (
    _format_conversation,
    get_compression_prompt,
)


def test_get_compression_prompt() -> None:
    """Test building compression prompt."""
    # Sample conversation
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello, I'm working on project X"},
        {"role": "assistant", "content": "Great! How can I help with project X?"},
    ]

    # Build prompt
    prompt_messages = get_compression_prompt(
        conversation_history=messages,
        user_instructions="Focus on project details",
    )

    # Verify structure
    assert len(prompt_messages) == 2
    assert prompt_messages[0]["role"] == "system"
    assert prompt_messages[1]["role"] == "user"

    # Verify system prompt contains key elements
    system_content = prompt_messages[0]["content"]
    assert "Today's date:" in system_content
    assert "compress" in system_content.lower()
    assert "context files" in system_content.lower()
    assert "Focus on project details" in system_content

    # Verify user prompt contains conversation
    user_content = prompt_messages[1]["role"]
    assert user_content == "user"


def test_format_conversation() -> None:
    """Test formatting conversation for review."""
    messages: list[dict] = [
        {"role": "system", "content": "System prompt"},
        {"role": "user", "content": "User message"},
        {"role": "assistant", "content": "Assistant response"},
        {
            "role": "assistant",
            "tool_calls": [{"function": {"name": "read_files"}}],
        },
        {"role": "tool", "name": "read_files", "content": "File contents here"},
    ]

    formatted = _format_conversation(messages)

    # Verify structure
    assert "# Conversation History" in formatted
    assert "**User:** User message" in formatted
    assert "**Assistant:** Assistant response" in formatted
    assert "[Called tool: read_files]" in formatted
    assert "**Tool Result (read_files):**" in formatted

    # Verify system prompt is not included
    assert "System prompt" not in formatted


def test_format_conversation_empty() -> None:
    """Test formatting empty conversation."""
    messages: list[dict] = []
    formatted = _format_conversation(messages)
    assert "# Conversation History" in formatted
