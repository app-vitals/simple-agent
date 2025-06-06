"""Tests for the tools registry module."""

from simple_agent.tools.registry import (
    execute_tool_call,
    get_tool_descriptions,
    requires_confirmation,
)


def test_get_tool_descriptions() -> None:
    """Test getting tool descriptions."""
    tool_descriptions = get_tool_descriptions()
    assert isinstance(tool_descriptions, list)
    assert len(tool_descriptions) > 0

    # Verify structure of the tool descriptions
    for tool_desc in tool_descriptions:
        assert tool_desc["type"] == "function"
        assert "function" in tool_desc
        assert "name" in tool_desc["function"]
        assert "description" in tool_desc["function"]
        assert "parameters" in tool_desc["function"]


def test_requires_confirmation() -> None:
    """Test tool confirmation requirements."""
    # Read files shouldn't require confirmation
    assert requires_confirmation("read_files") is False

    # Write file should require confirmation
    assert requires_confirmation("write_file") is True

    # Patch file should require confirmation
    assert requires_confirmation("patch_file") is True

    # Execute command should require confirmation
    assert requires_confirmation("execute_command") is True

    # Unknown tool should default to requiring confirmation
    assert requires_confirmation("unknown_tool") is True


def test_execute_tool_call() -> None:
    """Test executing a tool call."""
    # Test invalid tool name
    result = execute_tool_call("invalid_tool", {})
    assert isinstance(result, str)
    assert "Error" in result

    # Test read_files tool (using a mock)
    result = execute_tool_call("read_files", {"file_paths": ["/not/a/real/file.txt"]})
    assert isinstance(result, dict)  # Should return a dictionary
    assert "/not/a/real/file.txt" in result
    assert (
        result["/not/a/real/file.txt"] is None
    )  # Value should be None for non-existent file
