"""Tests for MCP tool adapter."""

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from simple_agent.tools.mcp.adapter import MCPToolAdapter
from simple_agent.tools.registry import TOOLS


@pytest.fixture
def mock_manager() -> MagicMock:
    """Create a mock MCP server manager."""
    manager = MagicMock()
    return manager


@pytest.fixture
def adapter(mock_manager: MagicMock) -> MCPToolAdapter:
    """Create an MCP tool adapter with mock manager."""
    return MCPToolAdapter(mock_manager)


def test_adapter_initialization(mock_manager: MagicMock) -> None:
    """Test adapter initializes with manager."""
    adapter = MCPToolAdapter(mock_manager)
    assert adapter.manager is mock_manager


def test_discover_and_register_tools_sync(
    adapter: MCPToolAdapter, mock_manager: MagicMock
) -> None:
    """Test discovering and registering tools from MCP server."""
    # Create mock tool
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.description = "A test tool"
    mock_tool.inputSchema = {
        "type": "object",
        "properties": {"arg1": {"type": "string", "description": "First argument"}},
    }

    mock_manager.list_tools_sync.return_value = [mock_tool]

    # Clear registry before test
    initial_tool_count = len(TOOLS)

    # Discover and register tools
    adapter.discover_and_register_tools_sync("test_server")

    # Verify list_tools was called
    mock_manager.list_tools_sync.assert_called_once_with("test_server")

    # Verify tool was registered
    assert "test_tool" in TOOLS
    assert len(TOOLS) == initial_tool_count + 1

    # Clean up
    del TOOLS["test_tool"]


def test_convert_input_schema_with_properties(adapter: MCPToolAdapter) -> None:
    """Test converting MCP input schema with properties."""
    input_schema = {
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "First argument"},
            "arg2": {"type": "number"},
        },
        "required": ["arg1"],
    }

    parameters, required = adapter._convert_input_schema(input_schema)

    assert "arg1" in parameters
    assert parameters["arg1"]["type"] == "string"
    assert parameters["arg1"]["description"] == "First argument"
    assert "arg2" in parameters
    # Should add default description
    assert parameters["arg2"]["description"] == "Parameter: arg2"
    # Should preserve required list
    assert required == ["arg1"]


def test_convert_input_schema_without_properties(adapter: MCPToolAdapter) -> None:
    """Test converting MCP input schema without properties."""
    input_schema = {"type": "object"}

    parameters, required = adapter._convert_input_schema(input_schema)

    assert parameters == {}
    assert required == []


def test_convert_input_schema_without_required(adapter: MCPToolAdapter) -> None:
    """Test converting MCP input schema without required field."""
    input_schema = {
        "type": "object",
        "properties": {
            "arg1": {"type": "string", "description": "First argument"},
        },
    }

    parameters, required = adapter._convert_input_schema(input_schema)

    assert "arg1" in parameters
    # If no required field, should return empty list
    assert required == []


def test_register_tool_with_optional_parameters(
    adapter: MCPToolAdapter, mock_manager: MagicMock
) -> None:
    """Test that tools with optional parameters are properly registered."""
    # Create mock tool with both required and optional parameters
    mock_tool = MagicMock()
    mock_tool.name = "test_optional_tool"
    mock_tool.description = "A tool with optional parameters"
    mock_tool.inputSchema = {
        "type": "object",
        "properties": {
            "required_param": {"type": "string", "description": "Required parameter"},
            "optional_param": {"type": "string", "description": "Optional parameter"},
        },
        "required": ["required_param"],
    }

    mock_manager.list_tools_sync.return_value = [mock_tool]

    # Register the tool
    adapter.discover_and_register_tools_sync("test_server")

    # Verify tool was registered with correct required list
    assert "test_optional_tool" in TOOLS
    assert TOOLS["test_optional_tool"]["required"] == ["required_param"]

    # Clean up
    del TOOLS["test_optional_tool"]


def test_tool_wrapper_execution(
    adapter: MCPToolAdapter, mock_manager: MagicMock, mocker: MockerFixture
) -> None:
    """Test that tool wrapper correctly calls MCP server."""
    # Mock display functions
    mocker.patch("simple_agent.tools.mcp.adapter.print_tool_call")

    # Create mock tool
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.description = "A test tool"
    mock_tool.inputSchema = {"type": "object", "properties": {}}

    # Mock the result from MCP server
    mock_content = MagicMock()
    mock_content.text = "test result"
    mock_manager.call_tool_sync.return_value = [mock_content]
    mock_manager.list_tools_sync.return_value = [mock_tool]

    # Register the tool
    adapter.discover_and_register_tools_sync("test_server")

    # Get the registered tool function
    tool_func = TOOLS["test_tool"]["function"]

    # Call the tool
    result = tool_func()

    # Verify MCP server was called
    mock_manager.call_tool_sync.assert_called_once_with("test_server", "test_tool", {})
    assert result == "test result"

    # Clean up
    del TOOLS["test_tool"]


def test_tool_wrapper_error_handling(
    adapter: MCPToolAdapter, mock_manager: MagicMock, mocker: MockerFixture
) -> None:
    """Test that tool wrapper handles errors gracefully."""
    # Mock display functions
    mocker.patch("simple_agent.tools.mcp.adapter.print_tool_call")
    mock_display_error = mocker.patch("simple_agent.tools.mcp.adapter.display_error")

    # Create mock tool
    mock_tool = MagicMock()
    mock_tool.name = "test_tool"
    mock_tool.description = "A test tool"
    mock_tool.inputSchema = {"type": "object", "properties": {}}

    # Mock the MCP server to raise an error
    mock_manager.call_tool_sync.side_effect = Exception("Test error")
    mock_manager.list_tools_sync.return_value = [mock_tool]

    # Register the tool
    adapter.discover_and_register_tools_sync("test_server")

    # Get the registered tool function
    tool_func = TOOLS["test_tool"]["function"]

    # Call the tool
    result = tool_func()

    # Verify error was displayed
    mock_display_error.assert_called_once()
    assert "error" in result
    assert "test_tool" in result["error"]

    # Clean up
    del TOOLS["test_tool"]
