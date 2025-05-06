"""Tests for the LLM client module."""

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


def test_send_completion_no_api_key(mocker: MockerFixture) -> None:
    """Test sending a completion with no API key."""
    # Mock display_error function
    mock_display_error = mocker.patch("simple_agent.llm.client.display_error")

    client = LLMClient(api_key=None)
    result = client.send_completion(messages=[])

    # Verify display_error was called
    mock_display_error.assert_called_once_with("No API key provided")
    assert result is None


def test_send_completion_success(client: LLMClient, mocker: MockerFixture) -> None:
    """Test sending a completion successfully."""
    # Create a mock response with the expected structure
    mock_response = mocker.MagicMock()
    mock_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(content="test response", tool_calls=None)
        )
    ]
    mock_completion = mocker.patch("litellm.completion", return_value=mock_response)

    messages = [{"role": "user", "content": "test message"}]
    result = client.send_completion(messages)

    assert result is mock_response
    # Verify LiteLLM was called with correct parameters
    mock_completion.assert_called_once()
    call_args = mock_completion.call_args[1]
    assert call_args["model"] == config.llm.model
    assert call_args["messages"] == messages
    assert call_args["api_key"] == "test_key"


def test_send_completion_with_tools(client: LLMClient, mocker: MockerFixture) -> None:
    """Test sending a completion with tools."""
    # Create a mock response
    mock_response = mocker.MagicMock()
    mock_response.choices = [
        mocker.MagicMock(
            message=mocker.MagicMock(content="test response", tool_calls=None)
        )
    ]
    mock_completion = mocker.patch("litellm.completion", return_value=mock_response)

    # Create mock tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "test_tool",
                "description": "A test tool",
                "parameters": {"type": "object", "properties": {}},
            },
        }
    ]

    messages = [{"role": "user", "content": "test message"}]
    result = client.send_completion(messages, tools=tools)

    assert result is mock_response
    # Verify tools were passed
    call_args = mock_completion.call_args[1]
    assert call_args["tools"] == tools
    assert call_args["tool_choice"] == "auto"


def test_send_completion_error(client: LLMClient, mocker: MockerFixture) -> None:
    """Test sending a completion with an error."""
    # Mock display_error function
    mock_display_error = mocker.patch("simple_agent.llm.client.display_error")

    # Mock LiteLLM to raise an exception
    mocker.patch("litellm.completion", side_effect=Exception("API error"))

    result = client.send_completion([{"role": "user", "content": "test message"}])

    # Verify display_error was called with the error message
    mock_display_error.assert_called_once_with("API Error: API error")
    assert result is None


def test_get_message_content(client: LLMClient, mocker: MockerFixture) -> None:
    """Test extracting content and tool calls from a response."""
    # Create a response with content but no tool calls
    mock_response = mocker.MagicMock()
    mock_message = mocker.MagicMock()
    mock_message.content = "test content"
    mock_message.tool_calls = None
    mock_response.choices = [mocker.MagicMock(message=mock_message)]

    content, tool_calls = client.get_message_content(mock_response)

    assert content == "test content"
    assert tool_calls is None

    # Create a response with tool calls
    mock_tool_call = mocker.MagicMock()
    mock_message = mocker.MagicMock()
    mock_message.content = None
    mock_message.tool_calls = [mock_tool_call]
    mock_response.choices = [mocker.MagicMock(message=mock_message)]

    content, tool_calls = client.get_message_content(mock_response)

    assert content is None
    assert tool_calls == [mock_tool_call]

    # Test with None response
    content, tool_calls = client.get_message_content(None)
    assert content is None
    assert tool_calls is None


def test_get_token_counts(client: LLMClient) -> None:
    """Test getting token counts and completion cost."""
    # Initialize with known values
    client.tokens_sent = 100
    client.tokens_received = 50
    client.completion_cost = 0.0025

    tokens_sent, tokens_received, cost = client.get_token_counts()

    assert tokens_sent == 100
    assert tokens_received == 50
    assert cost == 0.0025


def test_cost_calculation(client: LLMClient, mocker: MockerFixture) -> None:
    """Test that completion costs are calculated correctly."""
    # Create a mock response with token usage information
    mock_response = mocker.MagicMock()
    mock_response.usage.prompt_tokens = 100
    mock_response.usage.completion_tokens = 50

    # Mock litellm.completion to return our mock response
    mocker.patch("litellm.completion", return_value=mock_response)

    # Mock litellm.cost_per_token to return known costs
    mock_cost = mocker.patch("litellm.cost_per_token", return_value=(0.001, 0.0015))

    # Send a completion request
    messages = [{"role": "user", "content": "test message"}]
    client.send_completion(messages)

    # Verify cost_per_token was called with correct parameters
    mock_cost.assert_called_once_with(
        model=config.llm.model,
        prompt_tokens=100,
        completion_tokens=50,
    )

    # Verify token counters were updated
    assert client.tokens_sent == 100
    assert client.tokens_received == 50
    assert client.completion_cost == 0.0025  # 0.001 + 0.0015
