"""Tests for the agent module."""


import pytest
from pytest_mock import MockerFixture

from simple_agent.core.agent import HELP_TEXT, Agent


@pytest.fixture
def agent() -> Agent:
    """Create an agent for testing."""
    return Agent()


def test_agent_init(agent: Agent) -> None:
    """Test agent initialization."""
    assert agent.context == []
    assert hasattr(agent, "console")
    assert hasattr(agent, "llm_client")


def test_agent_run(agent: Agent, mocker: MockerFixture) -> None:
    """Test the agent run method."""
    # Mock the console to capture output
    agent.console = mocker.MagicMock()  # type: ignore

    # Mock _process_input to verify it's called
    agent._process_input = mocker.MagicMock()  # type: ignore

    # Create a mock input function that returns "test input" then "/exit"
    input_values = ["test input", "/exit"]

    def mock_input(prompt: str) -> str:
        return input_values.pop(0)

    # Run the agent with our mock input function
    agent.run(input_func=mock_input)

    # Verify the console was used to print the welcome message
    agent.console.print.assert_any_call(  # type: ignore
        "[bold green]Simple Agent[/bold green] ready. Type '/exit' to quit. Type '/help' for help."
    )

    # Verify _process_input was called with the test input
    agent._process_input.assert_called_once_with("test input")  # type: ignore


def test_agent_run_eof(agent: Agent, mocker: MockerFixture) -> None:
    """Test the agent run method with EOF (Ctrl+D)."""
    # Mock the console to capture output
    agent.console = mocker.MagicMock()  # type: ignore

    # Create a mock input function that raises EOFError
    def mock_input(prompt: str) -> str:
        raise EOFError()

    # Mock print to avoid interfering with test output
    mocker.patch("builtins.print")

    # Run the agent with our mock input function
    agent.run(input_func=mock_input)

    # Verify the EOF message was printed
    agent.console.print.assert_any_call("[yellow]Received EOF. Exiting.[/yellow]")  # type: ignore


def test_process_input_help(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _process_input method with /help command."""
    # Mock the console to capture output
    agent.console = mocker.MagicMock()  # type: ignore

    # Mock the help method
    agent._show_help = mocker.MagicMock()  # type: ignore

    # Process help command
    agent._process_input("/help")

    # Verify show_help was called
    agent._show_help.assert_called_once()  # type: ignore


def test_process_input_ai_request(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _process_input method with AI request."""
    # Mock the console to capture output
    agent.console = mocker.MagicMock()  # type: ignore

    # Mock the AI handler method
    agent._handle_ai_request = mocker.MagicMock()  # type: ignore

    # Process a regular message
    agent._process_input("What is the weather today?")

    # Verify AI handler was called with the message
    agent._handle_ai_request.assert_called_once_with("What is the weather today?")  # type: ignore


def test_show_help(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _show_help method."""
    # Mock the console to capture output
    agent.console = mocker.MagicMock()  # type: ignore

    # Call show help
    agent._show_help()

    # Verify console prints the help text
    agent.console.print.assert_called_once_with(HELP_TEXT)  # type: ignore


def test_handle_ai_request(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _handle_ai_request method."""
    # Mock the console and llm_client
    agent.console = mocker.MagicMock()  # type: ignore
    agent.llm_client = mocker.MagicMock()  # type: ignore
    agent.llm_client.send_message.return_value = "AI response"  # type: ignore

    # Call the method
    agent._handle_ai_request("Hello, AI")

    # Verify context was updated with user message
    assert {"role": "user", "content": "Hello, AI"} in agent.context

    # Verify LLM was called
    agent.llm_client.send_message.assert_called_once_with(  # type: ignore
        "Hello, AI", agent.context
    )

    # Verify response was displayed
    agent.console.print.assert_any_call("AI response")  # type: ignore

    # Verify context was updated with AI response
    assert {"role": "assistant", "content": "AI response"} in agent.context
