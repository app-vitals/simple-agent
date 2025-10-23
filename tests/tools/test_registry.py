"""Tests for the tools registry module."""

from simple_agent.tools.registry import (
    TOOLS,
    execute_tool_call,
    get_confirmation_handler,
    get_tool_descriptions,
    register,
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


def test_get_confirmation_handler() -> None:
    """Test getting confirmation handlers for tools."""
    # Write file should have a custom confirmation handler
    write_handler = get_confirmation_handler("write_file")
    assert write_handler is not None
    assert callable(write_handler)

    # Patch file should have a custom confirmation handler
    patch_handler = get_confirmation_handler("patch_file")
    assert patch_handler is not None
    assert callable(patch_handler)

    # Other tools shouldn't have a custom confirmation handler
    assert get_confirmation_handler("read_files") is None

    # Unknown tool should return None
    assert get_confirmation_handler("unknown_tool") is None


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


def test_register_with_optional_parameters() -> None:
    """Test that tools can be registered with optional parameters."""

    def test_tool(required_param: str, optional_param: str = "default") -> str:
        return f"{required_param}, {optional_param}"

    # Register tool with required list
    register(
        name="test_optional_tool",
        function=test_tool,
        description="Test tool with optional parameters",
        parameters={
            "required_param": {"type": "string", "description": "Required parameter"},
            "optional_param": {
                "type": "string",
                "description": "Optional parameter with default",
            },
        },
        returns="Test result",
        requires_confirmation=False,
        required=["required_param"],
    )

    # Verify tool was registered
    assert "test_optional_tool" in TOOLS
    assert TOOLS["test_optional_tool"]["required"] == ["required_param"]

    # Verify get_tool_descriptions includes proper required list
    descriptions = get_tool_descriptions()
    test_tool_desc = next(
        (d for d in descriptions if d["function"]["name"] == "test_optional_tool"), None
    )
    assert test_tool_desc is not None
    assert test_tool_desc["function"]["parameters"]["required"] == ["required_param"]

    # Clean up
    del TOOLS["test_optional_tool"]


def test_register_without_required_defaults_to_all() -> None:
    """Test that tools without required list default to all parameters required."""

    def test_tool_all_required(param1: str, param2: str) -> str:
        return f"{param1}, {param2}"

    # Register tool without required list (backwards compatibility)
    register(
        name="test_all_required",
        function=test_tool_all_required,
        description="Test tool with all params required",
        parameters={
            "param1": {"type": "string", "description": "First parameter"},
            "param2": {"type": "string", "description": "Second parameter"},
        },
        returns="Test result",
        requires_confirmation=False,
    )

    # Verify get_tool_descriptions defaults to all params required
    descriptions = get_tool_descriptions()
    test_tool_desc = next(
        (d for d in descriptions if d["function"]["name"] == "test_all_required"), None
    )
    assert test_tool_desc is not None
    # Should default to all parameters required for backwards compatibility
    assert set(test_tool_desc["function"]["parameters"]["required"]) == {
        "param1",
        "param2",
    }

    # Clean up
    del TOOLS["test_all_required"]
