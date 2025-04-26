"""Tests for the prompt module."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from simple_agent.cli.prompt import (
    CLI,
    CommandCompleter,
    create_rich_formatted_response,
    setup_keybindings,
)
from simple_agent.core.schema import AgentStatus


@pytest.fixture
def cli_instance() -> CLI:
    """Create a CLI instance for testing."""
    mock_process_input = MagicMock()
    return CLI(process_input_callback=mock_process_input)


def test_cli_init(cli_instance: CLI) -> None:
    """Test CLI initialization."""
    # Verify attributes are set
    assert hasattr(cli_instance, "console")
    assert hasattr(cli_instance, "process_input")
    assert hasattr(cli_instance, "style")
    assert hasattr(cli_instance, "session")


def test_command_completer() -> None:
    """Test the CommandCompleter class."""
    completer = CommandCompleter()

    # Verify commands contain the expected special commands
    assert "/help" in completer.commands
    assert "/exit" in completer.commands
    assert "/clear" in completer.commands
    assert "\\ + Enter" in completer.commands

    # Test getting completions
    doc = MagicMock()
    doc.get_word_before_cursor.return_value = "/"
    doc.text_before_cursor = "/"

    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) == 3  # /help, /exit, /clear

    # Test that slash commands only appear at the beginning of a line
    doc.text_before_cursor = "some text /"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) == 0  # No slash commands in the middle of text


def test_show_help(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the show_help method."""
    # Mock console.print
    mock_print = mocker.MagicMock()
    cli_instance.console.print = mock_print  # type: ignore

    # Call show_help
    cli_instance.show_help()

    # Verify console.print was called
    mock_print.assert_called_once()


def test_run_interactive_loop(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the run_interactive_loop method."""
    # Mock print_formatted_text
    mocker.patch("simple_agent.cli.prompt.print_formatted_text")

    # Mock session.prompt to return different values before raising EOFError to exit the loop
    # Test empty input, /help, /clear, normal input, and /exit
    prompt_values: list[str] = ["", "/help", "/clear", "test input", "/exit"]

    def mock_prompt(*args: Any, **kwargs: Any) -> str:
        if prompt_values:
            return prompt_values.pop(0)
        # When values run out, raise EOFError to exit the loop
        raise EOFError

    mock_session_prompt = MagicMock(side_effect=mock_prompt)
    cli_instance.session.prompt = mock_session_prompt  # type: ignore

    # Mock other methods
    mock_show_help = mocker.MagicMock()
    cli_instance.show_help = mock_show_help  # type: ignore

    mock_process_input = mocker.MagicMock()
    cli_instance.process_input = mock_process_input  # type: ignore

    mocker.patch("simple_agent.cli.prompt.clear")

    # Run the interactive loop
    cli_instance.run_interactive_loop()

    # Verify methods were called
    mock_process_input.assert_called_once_with("test input")
    mock_show_help.assert_called_once()


def test_run_interactive_loop_keyboard_interrupt(
    cli_instance: CLI, mocker: MockerFixture
) -> None:
    """Test handling of KeyboardInterrupt in run_interactive_loop."""
    # Mock print_formatted_text
    mock_print = mocker.patch("simple_agent.cli.prompt.print_formatted_text")

    # Mock session.prompt to raise KeyboardInterrupt
    mock_session_prompt = MagicMock(side_effect=KeyboardInterrupt())
    cli_instance.session.prompt = mock_session_prompt  # type: ignore

    # Run the loop and expect it to exit gracefully
    cli_instance.run_interactive_loop()

    # Verify print was called
    assert (
        mock_print.call_count >= 1
    )  # At least once for welcome and once for interrupt message


def test_integration_with_agent(mocker: MockerFixture) -> None:
    """Test integration with Agent class."""
    # Create mock process_input callback
    mock_process_input = mocker.MagicMock()

    # Create CLI with the mock callback
    cli = CLI(process_input_callback=mock_process_input)

    # Setup prompt to return a test input and then exit
    mock_prompt = mocker.MagicMock(side_effect=["test command", "/exit"])
    cli.session.prompt = mock_prompt  # type: ignore

    # Mock print_formatted_text to avoid console output
    mocker.patch("simple_agent.cli.prompt.print_formatted_text")

    # Run the interactive loop
    cli.run_interactive_loop()

    # Verify that the process_input callback was called with the test input
    mock_process_input.assert_called_once_with("test command")


def test_multiline_input(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test multiline input with the prompt continuation feature."""
    # Test the prompt_continuation function
    # Simply verify that the prompt_continuation is set up correctly
    assert hasattr(cli_instance.session, "prompt_continuation")
    assert cli_instance.session.prompt_continuation is not None

    # Test the Enter key handler for backslash continuation indirectly
    # by verifying session configuration
    assert cli_instance.session.multiline

    # Directly test the Enter key handler from setup_keybindings
    kb = setup_keybindings()
    assert kb is not None
    assert len(kb.bindings) >= 3  # At least Ctrl+C, Ctrl+D, and Enter


def test_run_interactive_loop_eof(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test handling of EOFError in run_interactive_loop."""
    # Mock print_formatted_text
    mock_print = mocker.patch("simple_agent.cli.prompt.print_formatted_text")

    # Mock session.prompt to raise EOFError
    mock_session_prompt = MagicMock(side_effect=EOFError())
    cli_instance.session.prompt = mock_session_prompt  # type: ignore

    # Run the loop and expect it to exit gracefully
    cli_instance.run_interactive_loop()

    # Verify print was called
    assert (
        mock_print.call_count >= 1
    )  # At least once for welcome and once for EOF message


def test_create_rich_formatted_response() -> None:
    """Test the create_rich_formatted_response function."""
    # Test with COMPLETE status
    complete_response = {
        "message": "This is a test message",
        "status": AgentStatus.COMPLETE,
        "next_action": None,
    }

    formatted = create_rich_formatted_response(complete_response)
    assert "This is a test message" in formatted
    assert "Next action" not in formatted

    # Test with CONTINUE status
    continue_response = {
        "message": "Working on your request",
        "status": AgentStatus.CONTINUE,
        "next_action": "I will check the documentation next",
    }

    formatted = create_rich_formatted_response(continue_response)
    assert "Working on your request" in formatted
    assert "Next action" in formatted
    assert "I will check the documentation next" in formatted

    # Test with ASK status
    ask_response = {
        "message": "I found multiple options",
        "status": AgentStatus.ASK,
        "next_action": "Which option do you prefer?",
    }

    formatted = create_rich_formatted_response(ask_response)
    assert "I found multiple options" in formatted
    assert "Question" in formatted
    assert "Which option do you prefer?" in formatted
