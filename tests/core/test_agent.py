"""Tests for the agent module."""


import pytest
from pytest_mock import MockerFixture

from simple_agent.core.agent import Agent


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

    # Create a mock input function that returns "test input" then "exit"
    input_values = ["test input", "exit"]

    def mock_input(prompt: str) -> str:
        return input_values.pop(0)

    # Run the agent with our mock input function
    agent.run(input_func=mock_input)

    # Verify the console was used to print the welcome message
    agent.console.print.assert_any_call(  # type: ignore
        "[bold green]Simple Agent[/bold green] ready. Type 'exit' to quit."
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


def test_process_input(agent: Agent, mocker: MockerFixture) -> None:
    """Test the _process_input method."""
    # Mock the console to capture output
    agent.console = mocker.MagicMock()  # type: ignore

    # Process some input
    agent._process_input("test input")

    # Verify the console was used to print the received message
    agent.console.print.assert_called_once_with("Received: test input")  # type: ignore
