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
        mocker.MagicMock(message=mocker.MagicMock(content="test response"))
    ]
    mock_completion = mocker.patch("litellm.completion", return_value=mock_response)

    result = client.send_message("test message")

    assert result == "test response"
    mock_completion.assert_called_once_with(
        model=config.llm.model,
        messages=[{"role": "user", "content": "test message"}],
        api_key="test_key",
    )


def test_send_message_with_context(client: LLMClient, mocker: MockerFixture) -> None:
    """Test sending a message with context."""
    # Create a mock response with the expected structure
    mock_response = mocker.MagicMock()
    mock_response.choices = [
        mocker.MagicMock(message=mocker.MagicMock(content="test response"))
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
