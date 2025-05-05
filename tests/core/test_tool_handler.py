"""Tests for the tool handler module."""

import json
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture
from rich.console import Console

from simple_agent.core.tool_handler import ToolHandler, get_tools_for_llm


def test_get_tools_for_llm() -> None:
    """Test getting tools in LLM format."""
    # We're testing a simple forwarding function, so we can just
    # check it returns valid tool definitions
    tools = get_tools_for_llm()

    # Check it's a list of valid tool definitions
    assert isinstance(tools, list)
    assert len(tools) > 0
    # Each tool should have type and function fields
    assert all("type" in tool for tool in tools)
    assert all("function" in tool for tool in tools)
    # Each function should have a name and parameters
    assert all("name" in tool["function"] for tool in tools)
    assert all("parameters" in tool["function"] for tool in tools)


class TestToolHandler:
    """Tests for the ToolHandler class."""

    @pytest.fixture
    def handler(self) -> ToolHandler:
        """Create a tool handler for testing."""
        return ToolHandler()

    def test_init(self, handler: ToolHandler) -> None:
        """Test initialization."""
        # Check only that input_func is set correctly
        # Note: console is now imported from display module, not an attribute of ToolHandler
        assert handler.input_func is input

    def test_format_value(self, handler: ToolHandler) -> None:
        """Test _format_value method."""
        # Short string
        assert handler._format_value("test") == "test"

        # Long string should be truncated
        long_string = "x" * 200
        assert handler._format_value(long_string) == "x" * 97 + "..."

        # Non-string value
        assert handler._format_value(123) == "123"

    def test_process_tool_calls_no_confirmation(
        self, handler: ToolHandler, mocker: MockerFixture
    ) -> None:
        """Test processing tool calls that don't require confirmation."""
        # Mock the necessary functions
        mock_requires_confirmation = mocker.patch(
            "simple_agent.core.tool_handler.requires_confirmation", return_value=False
        )
        mock_execute_tool_call = mocker.patch(
            "simple_agent.core.tool_handler.execute_tool_call",
            return_value="test result",
        )

        # Create a mock tool call
        mock_tool_call = mocker.MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = json.dumps({"arg": "value"})

        # Initial messages
        messages = [{"role": "user", "content": "test"}]

        # Process the tool call
        result = handler.process_tool_calls([mock_tool_call], messages)

        # Verify the functions were called correctly
        mock_requires_confirmation.assert_called_once_with("test_tool")
        mock_execute_tool_call.assert_called_once_with("test_tool", {"arg": "value"})

        # Verify the result contains the original message plus the tool response
        assert len(result) == 2
        assert result[0] == {"role": "user", "content": "test"}
        assert result[1]["role"] == "tool"
        assert result[1]["tool_call_id"] == "call_123"
        assert result[1]["name"] == "test_tool"
        assert result[1]["content"] == "test result"

    def test_process_tool_calls_with_confirmation_yes(
        self, handler: ToolHandler, mocker: MockerFixture
    ) -> None:
        """Test processing tool calls with confirmation (user responds yes)."""
        # Mock the necessary functions
        mocker.patch(
            "simple_agent.core.tool_handler.requires_confirmation", return_value=True
        )
        mocker.patch(
            "simple_agent.core.tool_handler.execute_tool_call",
            return_value="test result",
        )
        # Mock get_confirmation from display module instead of directly using console
        mocker.patch(
            "simple_agent.core.tool_handler.get_confirmation",
            return_value=True  # Simulate user confirming
        )

        # Mock the input function to return 'y'
        mock_input = mocker.MagicMock(return_value="y")
        handler.input_func = mock_input

        # Create a mock tool call
        mock_tool_call = mocker.MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = json.dumps({"arg": "value"})

        # Process the tool call
        result = handler.process_tool_calls([mock_tool_call], [])

        # Verify the user was asked for confirmation with the updated prompt
        mock_input.assert_called_once_with("Confirm test_tool(arg='value')? [Y/n] ")

        # Verify the result contains the tool response
        assert len(result) == 1
        assert result[0]["role"] == "tool"
        assert result[0]["tool_call_id"] == "call_123"
        assert result[0]["content"] == "test result"

    def test_process_tool_calls_with_confirmation_no(
        self, handler: ToolHandler, mocker: MockerFixture
    ) -> None:
        """Test processing tool calls with confirmation (user responds no)."""
        # Mock the necessary functions
        mocker.patch(
            "simple_agent.core.tool_handler.requires_confirmation", return_value=True
        )
        mock_execute = mocker.patch("simple_agent.core.tool_handler.execute_tool_call")
        
        # Mock get_confirmation from display module
        mocker.patch(
            "simple_agent.core.tool_handler.get_confirmation",
            return_value=False  # Simulate user denying
        )

        # Mock the input function to return 'n'
        mock_input = mocker.MagicMock(return_value="n")
        handler.input_func = mock_input

        # Create a mock tool call
        mock_tool_call = mocker.MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = json.dumps({"arg": "value"})

        # Process the tool call
        result = handler.process_tool_calls([mock_tool_call], [])

        # Verify execute_tool_call was not called
        mock_execute.assert_not_called()

        # Verify the result contains the rejection message
        assert len(result) == 1
        assert result[0]["role"] == "tool"
        assert result[0]["tool_call_id"] == "call_123"
        assert "denied permission" in result[0]["content"]

    def test_process_tool_calls_invalid_arguments(
        self, handler: ToolHandler, mocker: MockerFixture
    ) -> None:
        """Test processing tool calls with invalid arguments."""
        # Mock display_error from display module
        mock_display_error = mocker.patch("simple_agent.core.tool_handler.display_error")

        # Create a mock tool call with invalid JSON arguments
        mock_tool_call = mocker.MagicMock()
        mock_tool_call.id = "call_123"
        mock_tool_call.function.name = "test_tool"
        mock_tool_call.function.arguments = "{invalid json"

        # Process the tool call
        result = handler.process_tool_calls([mock_tool_call], [])

        # Verify the result contains the error message
        assert len(result) == 1
        assert result[0]["role"] == "tool"
        assert result[0]["tool_call_id"] == "call_123"
        assert "Could not parse tool arguments" in result[0]["content"]
