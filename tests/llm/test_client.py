"""Tests for the LLM client module."""

import json

import pytest
from pytest_mock import MockerFixture

from simple_agent.config import config
from simple_agent.llm.client import LLMClient


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> LLMClient:
    """Create a client for testing."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test_key")
    # Need to manually update config since it's loaded at import time
    config.llm.api_key = "test_key"
    return LLMClient()


def test_client_init(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test client initialization."""
    # Test with explicit API key
    client = LLMClient(api_key="test_key")
    assert client.api_key == "test_key"

    # Test with environment variable
    monkeypatch.setenv("ANTHROPIC_API_KEY", "env_key")
    # Need to manually update config since it's loaded at import time
    config.llm.api_key = "env_key"
    client = LLMClient()
    assert client.api_key == "env_key"

    # Test with no API key
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Need to manually update config
    config.llm.api_key = None
    client = LLMClient()
    assert client.api_key is None


def test_send_message_no_api_key(mocker: MockerFixture) -> None:
    """Test sending a message with no API key."""
    client = LLMClient(api_key=None)
    client.console = mocker.MagicMock()  # type: ignore

    result = client.send_message("test message")

    assert result is None
    client.console.print.assert_called_once_with(  # type: ignore
        "[bold red]Error:[/bold red] No API key provided"
    )


def test_send_message_success(client: LLMClient, mocker: MockerFixture) -> None:
    """Test sending a message successfully."""
    # Create a mock response with the expected structure
    mock_response = mocker.MagicMock()
    mock_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(content="test response", tool_calls=None)
        )
    ]
    mock_completion = mocker.patch("litellm.completion", return_value=mock_response)

    result = client.send_message("test message")

    assert result == "test response"
    mock_completion.assert_called_once_with(
        model=config.llm.model,
        messages=[{"role": "user", "content": "test message"}],
        tools=client.tools,
        tool_choice="auto",
        api_key="test_key",
    )


def test_send_message_with_context(client: LLMClient, mocker: MockerFixture) -> None:
    """Test sending a message with context."""
    # Create a mock response with the expected structure
    mock_response = mocker.MagicMock()
    mock_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(content="test response", tool_calls=None)
        )
    ]
    mock_completion = mocker.patch("litellm.completion", return_value=mock_response)

    context = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
    ]

    # Create a copy to avoid modifying the original context
    context_copy = context.copy()

    result = client.send_message("How are you?", context=context_copy)

    assert result == "test response"

    # Verify the LLM was called (without checking exact messages to avoid test fragility)
    mock_completion.assert_called_once()

    # Check the model and API key were passed correctly
    call_args = mock_completion.call_args[1]
    assert call_args["model"] == config.llm.model
    assert call_args["api_key"] == "test_key"
    assert call_args["tools"] == client.tools
    assert call_args["tool_choice"] == "auto"

    # Check that the message was included in the call
    assert {"role": "user", "content": "How are you?"} in call_args["messages"]


def test_send_message_error(client: LLMClient, mocker: MockerFixture) -> None:
    """Test sending a message with an error."""
    mocker.patch("litellm.completion", side_effect=Exception("API error"))
    client.console = mocker.MagicMock()  # type: ignore

    result = client.send_message("test message")

    assert result is None
    client.console.print.assert_called_once_with(  # type: ignore
        "[bold red]API Error:[/bold red] API error"
    )


def test_tool_calls_handling(client: LLMClient, mocker: MockerFixture) -> None:
    """Test handling tool calls in the response."""
    # Mock the message content with tool calls
    mock_tool_call = mocker.MagicMock()
    mock_tool_call.id = "call_123"
    mock_tool_call.function.name = "read_file"
    mock_tool_call.function.arguments = json.dumps({"file_path": "/test/file.txt"})

    mock_message = mocker.MagicMock()
    mock_message.tool_calls = [mock_tool_call]
    mock_message.model_dump.return_value = {
        "content": None,
        "tool_calls": [{"id": "call_123"}],
    }

    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock(message=mock_message)]

    # Mock the final response after tool execution
    mock_final_message = mocker.MagicMock()
    mock_final_message.content = "Tool executed successfully"
    mock_final_message.tool_calls = None

    mock_final_response = mocker.MagicMock()
    mock_final_response.choices = [mocker.MagicMock(message=mock_final_message)]

    # Mock completion and tool execution
    mock_completion = mocker.patch("litellm.completion")
    mock_completion.side_effect = [mock_response, mock_final_response]

    # Mock tool-related functions
    mocker.patch("simple_agent.tools.execute_tool_call", return_value="File content")
    mocker.patch("simple_agent.tools.requires_confirmation", return_value=False)

    client.console = mocker.MagicMock()  # type: ignore

    # Call method
    result = client.send_message("Read a file", context=[])

    # Verify result
    assert result == "Tool executed successfully"

    # Verify tool execution was attempted
    assert (
        mock_completion.call_count == 2
    )  # Initial call + follow-up after tool execution

    # Verify tool response was added to messages
    second_call_messages = mock_completion.call_args_list[1][1]["messages"]
    assert any(
        m.get("role") == "tool" and m.get("tool_call_id") == "call_123"
        for m in second_call_messages
    )


def test_tool_calls_user_confirmation(client: LLMClient, mocker: MockerFixture) -> None:
    """Test tool calls with user confirmation."""
    # Mock tool call that requires confirmation
    mock_tool_call = mocker.MagicMock()
    mock_tool_call.id = "call_456"
    mock_tool_call.function.name = "execute_command"
    mock_tool_call.function.arguments = json.dumps({"command": "ls -la"})

    mock_message = mocker.MagicMock()
    mock_message.tool_calls = [mock_tool_call]
    mock_message.model_dump.return_value = {
        "content": None,
        "tool_calls": [{"id": "call_456"}],
    }

    mock_response = mocker.MagicMock()
    mock_response.choices = [mocker.MagicMock(message=mock_message)]

    mock_final_response = mocker.MagicMock()
    mock_final_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(content="Command executed", tool_calls=None)
        )
    ]

    # Mock confirmation input function to return 'y'
    mock_input = mocker.MagicMock(return_value="y")

    # Mock completion, tools, and console
    mock_completion = mocker.patch("litellm.completion")
    mock_completion.side_effect = [mock_response, mock_final_response]

    mocker.patch("simple_agent.tools.requires_confirmation", return_value=True)
    mocker.patch("simple_agent.tools.execute_tool_call", return_value=("stdout", "", 0))

    client.console = mocker.MagicMock()  # type: ignore

    # Call method with our mock input function
    result = client.send_message("Run ls command", context=[], input_func=mock_input)

    # Verify confirmation was requested
    mock_input.assert_called_once()
    assert "confirm" in mock_input.call_args[0][0].lower()

    # Verify result
    assert result == "Command executed"
