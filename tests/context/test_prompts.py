"""Tests for context extraction prompts."""

from simple_agent.context.prompts import get_context_extraction_prompt


def test_get_context_extraction_prompt_with_user_message() -> None:
    """Test generating prompt with user message."""
    prompt = get_context_extraction_prompt(user_message="Fix the auth bug")

    assert "Fix the auth bug" in prompt
    assert "User Message:" in prompt
    assert "Analyze this interaction" in prompt


def test_get_context_extraction_prompt_with_tool_calls() -> None:
    """Test generating prompt with tool calls."""
    tool_calls = [
        {"name": "read_files", "arguments": {"file_paths": ["test.py", "main.py"]}},
    ]

    prompt = get_context_extraction_prompt(tool_calls=tool_calls)

    assert "Tools Executed:" in prompt
    assert "read_files" in prompt


def test_get_context_extraction_prompt_with_both() -> None:
    """Test generating prompt with both message and tool calls."""
    tool_calls = [{"name": "write_file", "arguments": {"file_path": "output.py"}}]

    prompt = get_context_extraction_prompt(
        user_message="Create output file", tool_calls=tool_calls
    )

    assert "Create output file" in prompt
    assert "write_file" in prompt
    assert "User Message:" in prompt
    assert "Tools Executed:" in prompt


def test_get_context_extraction_prompt_empty() -> None:
    """Test generating prompt with no input."""
    prompt = get_context_extraction_prompt()

    assert "No interaction to analyze" in prompt


def test_get_context_extraction_prompt_long_args() -> None:
    """Test that long arguments are truncated."""
    tool_calls = [
        {
            "name": "write_file",
            "arguments": {"content": "A" * 100, "file_path": "test.py"},
        }
    ]

    prompt = get_context_extraction_prompt(tool_calls=tool_calls)

    # Should truncate long content
    assert "..." in prompt or "100" not in prompt


def test_get_context_extraction_prompt_many_args() -> None:
    """Test that only first 3 arguments are shown."""
    tool_calls = [
        {
            "name": "test_tool",
            "arguments": {"arg1": "a", "arg2": "b", "arg3": "c", "arg4": "d"},
        }
    ]

    prompt = get_context_extraction_prompt(tool_calls=tool_calls)

    # Should show max 3 args
    assert "test_tool" in prompt
