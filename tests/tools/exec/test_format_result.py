"""Tests for execute_command format_result function."""

from simple_agent.tools.exec.execute_command import format_execute_command_result


def test_format_execute_command_with_stdout() -> None:
    """Test formatting execute_command result with stdout."""
    content = "('Hello World\\n', '', 0)"
    result = format_execute_command_result(content)
    assert "Hello World" in result
    assert "[dim]" in result


def test_format_execute_command_with_stderr() -> None:
    """Test formatting execute_command result with stderr."""
    content = "('', 'Error message\\n', 1)"
    result = format_execute_command_result(content)
    assert "Error message" in result
    assert "[red]" in result


def test_format_execute_command_with_invalid_format() -> None:
    """Test formatting with invalid tuple format."""
    content = "invalid content"
    result = format_execute_command_result(content)
    # Should fallback to dim formatting
    assert "[dim]" in result
    assert "invalid content" in result


def test_format_execute_command_with_empty_output() -> None:
    """Test formatting execute_command with empty output."""
    content = "('', '', 0)"
    result = format_execute_command_result(content)
    # Should return dim formatted content when both stdout and stderr are empty
    assert "[dim]" in result
