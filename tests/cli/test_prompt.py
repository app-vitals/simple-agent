"""Tests for the prompt module."""

from typing import Any
from unittest.mock import MagicMock

import pytest
from prompt_toolkit.keys import Keys
from pytest_mock import MockerFixture

from simple_agent.cli.prompt import (
    CLI,
    CLIMode,
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


def test_cli_init_history_fallback(mocker: MockerFixture) -> None:
    """Test CLI initialization with history file fallback."""
    # Mock FileHistory to raise an exception
    mock_file_history = mocker.patch("simple_agent.cli.prompt.FileHistory")
    mock_file_history.side_effect = Exception("Cannot create history file")

    # Mock process_input callback
    mock_process_input = mocker.MagicMock()

    # Create CLI - this should fall back to no history
    cli = CLI(process_input_callback=mock_process_input)

    # Verify attributes are still set
    assert hasattr(cli, "console")
    assert hasattr(cli, "process_input")
    assert hasattr(cli, "style")
    assert hasattr(cli, "session")


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

    # Test the prompt_continuation function directly
    # Get the prompt_continuation callable from the session
    # The mypy error is because prompt_continuation could be multiple types,
    # but we know it's a callable in this context
    prompt_cont = cli_instance.session.prompt_continuation

    # Test prompt_continuation with different inputs - ensure it's a callable
    if callable(prompt_cont):
        # For not soft-wrapped lines - call the function to get the result
        result_no_wrap = prompt_cont(80, 1, False)
        assert result_no_wrap == "  "  # Should return 2 spaces for indentation

        # For soft-wrapped lines
        result_wrap = prompt_cont(80, 1, True)
        assert result_wrap == ""  # Should return empty string for soft-wrapped lines

    # Test the Enter key handler for backslash continuation indirectly
    # by verifying session configuration
    assert cli_instance.session.multiline

    # Directly test the Enter key handler from setup_keybindings
    kb = setup_keybindings(cli_instance)
    assert kb is not None
    assert len(kb.bindings) >= 5  # Ctrl+C, Ctrl+D, Enter, !, and Backspace keys


def test_bang_key_handler(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the '!' key binding functionality."""
    # Get key bindings
    kb = setup_keybindings(cli_instance)

    # Create mock event and buffer for testing
    mock_buffer = mocker.MagicMock()
    mock_app = mocker.MagicMock()
    mock_event = mocker.MagicMock()
    mock_event.app = mock_app
    mock_event.app.current_buffer = mock_buffer
    mock_event.current_buffer = mock_buffer
    mock_event.key_sequence = [None]  # Just to have something

    # Find the ! handler
    bang_handler = None
    for binding in kb.bindings:
        if binding.keys[0] == "!":
            bang_handler = binding.handler
            break

    assert bang_handler is not None

    # Test '!' handler for changing modes
    cli_instance.mode = CLIMode.NORMAL
    bang_handler(mock_event)
    assert cli_instance.mode == CLIMode.SHELL

    # Test '!' handler in Shell mode - should insert ! character
    cli_instance.mode = CLIMode.SHELL
    # Reset the mock_buffer to clear any state from previous tests
    mock_buffer.reset_mock()

    # Mock set_mode method to return False (meaning already in shell mode)
    mock_set_mode = mocker.patch.object(cli_instance, "set_mode", return_value=False)

    # Call the bang handler
    bang_handler(mock_event)

    # Now the insert_text should have been called
    mock_buffer.insert_text.assert_called_once_with("!")

    # Verify our mock was called
    mock_set_mode.assert_called_once_with(CLIMode.SHELL)


def test_backspace_handler(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the Backspace key handler functionality."""
    # Get key bindings
    kb = setup_keybindings(cli_instance)

    # Create mock event and buffer for testing
    mock_buffer = mocker.MagicMock()
    mock_app = mocker.MagicMock()
    mock_event = mocker.MagicMock()
    mock_event.app = mock_app
    mock_event.app.current_buffer = mock_buffer
    mock_event.current_buffer = mock_buffer

    # Find the Backspace handler
    backspace_handler = None
    for binding in kb.bindings:
        if binding.keys[0] == Keys.Backspace:
            backspace_handler = binding.handler
            break

    assert backspace_handler is not None

    # Test Backspace handler - reset to normal mode if buffer empty
    cli_instance.mode = CLIMode.SHELL
    mock_buffer.cursor_position = 0  # Simulate cursor at beginning
    mock_buffer.reset_mock()

    # Need to mock set_mode to return True (mode was changed)
    mock_set_mode = mocker.patch.object(cli_instance, "set_mode", return_value=True)

    backspace_handler(mock_event)

    # Verify set_mode was called with NORMAL mode
    mock_set_mode.assert_called_once_with(CLIMode.NORMAL)

    # Test should not delete character when changing modes
    mock_buffer.delete_before_cursor.assert_not_called()

    # Test Backspace handler - normal delete functionality when not at start
    cli_instance.mode = CLIMode.NORMAL
    mock_buffer.cursor_position = 3  # Not at beginning
    mock_buffer.reset_mock()
    mock_set_mode.reset_mock()

    backspace_handler(mock_event)

    # Should not try to change mode
    mock_set_mode.assert_not_called()
    # Should delete character
    mock_buffer.delete_before_cursor.assert_called_once_with(1)


def test_ctrl_c_handler(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the Ctrl+C key handler functionality."""
    # Get key bindings
    kb = setup_keybindings(cli_instance)

    # Create mock event and buffer for testing
    mock_buffer = mocker.MagicMock()
    mock_app = mocker.MagicMock()
    mock_event = mocker.MagicMock()
    mock_event.app = mock_app
    mock_event.app.current_buffer = mock_buffer

    # Find the Ctrl+C handler
    ctrl_c_handler = None
    for binding in kb.bindings:
        if binding.keys[0] == Keys.ControlC:
            ctrl_c_handler = binding.handler
            break

    assert ctrl_c_handler is not None

    # Test Ctrl+C handler with text in buffer
    cli_instance.mode = CLIMode.SHELL
    mock_buffer.text = "test text"

    # Mock set_mode to handle the mode change
    mock_set_mode = mocker.patch.object(cli_instance, "set_mode")

    ctrl_c_handler(mock_event)

    # Should clear buffer
    assert mock_buffer.text == ""
    # Should reset to normal mode
    mock_set_mode.assert_called_once_with(CLIMode.NORMAL)

    # Test Ctrl+C handler with empty buffer and normal mode (should exit)
    cli_instance.mode = CLIMode.NORMAL
    mock_buffer.text = ""
    mock_app.exit.reset_mock()
    mock_set_mode.reset_mock()

    ctrl_c_handler(mock_event)

    # Should cause app to exit
    mock_app.exit.assert_called_once()
    # KeyboardInterrupt should be passed
    args, kwargs = mock_app.exit.call_args
    assert isinstance(kwargs.get("exception"), KeyboardInterrupt)


def test_ctrl_d_handler(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the Ctrl+D key handler functionality."""
    # Get key bindings
    kb = setup_keybindings(cli_instance)

    # Create mock event and buffer for testing
    mock_app = mocker.MagicMock()
    mock_event = mocker.MagicMock()
    mock_event.app = mock_app

    # Find the Ctrl+D handler
    ctrl_d_handler = None
    for binding in kb.bindings:
        if binding.keys[0] == Keys.ControlD:
            ctrl_d_handler = binding.handler
            break

    assert ctrl_d_handler is not None

    # Test Ctrl+D handler (should exit with EOFError)
    mock_app.exit.reset_mock()
    ctrl_d_handler(mock_event)

    # Check that exit was called
    assert mock_app.exit.call_count == 1
    # Check that exception is EOFError
    args, kwargs = mock_app.exit.call_args
    assert isinstance(kwargs.get("exception"), EOFError)


def test_enter_handler(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the Enter key handler functionality."""
    # Get key bindings
    kb = setup_keybindings(cli_instance)

    # Create mock event and buffer for testing
    mock_buffer = mocker.MagicMock()
    mock_event = mocker.MagicMock()
    mock_event.app = mocker.MagicMock()
    mock_event.app.current_buffer = mock_buffer
    mock_event.current_buffer = mock_buffer

    # Find the Enter handler
    enter_handler = None
    for binding in kb.bindings:
        if binding.keys[0] == Keys.Enter:
            enter_handler = binding.handler
            break

    assert enter_handler is not None

    # Test Enter handler with backslash continuation
    mock_buffer.document.current_line = "test line \\"
    cli_instance.mode = CLIMode.NORMAL
    mock_buffer.reset_mock()

    enter_handler(mock_event)

    # Should delete the backslash
    mock_buffer.delete_before_cursor.assert_called_once_with(1)
    # Should insert a newline
    mock_buffer.newline.assert_called_once()

    # Test Enter handler with backslash continuation in shell mode
    mock_buffer.document.current_line = "echo foo \\"
    cli_instance.mode = CLIMode.SHELL
    mock_buffer.reset_mock()

    enter_handler(mock_event)

    # Should not delete the backslash in shell mode
    mock_buffer.delete_before_cursor.assert_not_called()
    # Should insert a newline
    mock_buffer.newline.assert_called_once()

    # Test normal Enter behavior (no backslash)
    mock_buffer.document.current_line = "normal line"
    mock_buffer.reset_mock()

    enter_handler(mock_event)

    # Should validate and handle
    mock_buffer.validate_and_handle.assert_called_once()


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


def test_set_mode(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the set_mode method."""
    # Mock session to avoid app.invalidate() calls
    mock_app = mocker.MagicMock()
    cli_instance.session.app = mock_app  # type: ignore
    cli_instance.session.message = None  # type: ignore

    # Test switching from NORMAL to SHELL
    assert cli_instance.mode == CLIMode.NORMAL
    result = cli_instance.set_mode(CLIMode.SHELL)
    assert result is True  # Mode was changed
    assert cli_instance.mode == CLIMode.SHELL

    # Test trying to set the same mode (should return False)
    result = cli_instance.set_mode(CLIMode.SHELL)
    assert result is False  # Mode was not changed
    assert cli_instance.mode == CLIMode.SHELL

    # Test switching back to NORMAL
    result = cli_instance.set_mode(CLIMode.NORMAL)
    assert result is True  # Mode was changed
    assert cli_instance.mode == CLIMode.NORMAL

    # Test invalid mode
    with pytest.raises(ValueError):
        # Need to use type ignore as mypy will catch this error
        cli_instance.set_mode("invalid_mode")  # type: ignore


def test_execute_command(cli_instance: CLI, mocker: MockerFixture) -> None:
    """Test the execute_command method."""
    # Mock subprocess.run
    mock_result = mocker.MagicMock()
    mock_result.stdout = "command output"
    mock_result.stderr = "error output"

    mock_run = mocker.patch("subprocess.run", return_value=mock_result)

    # Test normal command execution
    output = cli_instance.execute_command("test command")

    # Verify subprocess.run was called correctly
    mock_run.assert_called_once_with(
        "test command",
        shell=True,
        capture_output=True,
        text=True,
        check=False,
    )

    # Verify output format includes both stdout and stderr
    assert "command output" in output
    assert "error output" in output

    # Test with only stdout, no stderr
    mock_result.stderr = ""
    mock_run.reset_mock()
    mock_run.return_value = mock_result
    mock_run.side_effect = None  # Clear any previous side effects

    output = cli_instance.execute_command("stdout only command")
    assert "command output" in output
    assert "error output" not in output

    # Test with only stderr, no stdout
    mock_result.stdout = ""
    mock_result.stderr = "error only"
    mock_run.reset_mock()
    mock_run.return_value = mock_result

    output = cli_instance.execute_command("stderr only command")
    assert "error only" in output
    assert "command output" not in output

    # Test exception handling
    mock_run.side_effect = Exception("test error")
    output = cli_instance.execute_command("problem command")
    assert "Error executing command: test error" in output


def test_shell_mode_in_interactive_loop(
    cli_instance: CLI, mocker: MockerFixture
) -> None:
    """Test shell command handling in interactive mode."""
    # Mock print_formatted_text to avoid console output
    mocker.patch("simple_agent.cli.prompt.print_formatted_text")

    # Mock set_mode method to track calls and avoid real mode switching
    # Use mocker.patch.object with wraps to track calls while preserving behavior
    mock_set_mode = mocker.patch.object(
        cli_instance, "set_mode", wraps=cli_instance.set_mode
    )

    # Mock session.prompt for different input scenarios
    mock_prompt = mocker.MagicMock()
    # First return normal mode prompt, then mock shell mode
    cli_instance.session.prompt = mock_prompt  # type: ignore

    # Test with shell command first (like "ls"), then exit
    mock_prompt.side_effect = ["ls", "/exit"]

    # Mock execute_command to avoid real command execution
    mock_execute = mocker.MagicMock(return_value="command output")
    cli_instance.execute_command = mock_execute  # type: ignore

    # Mock process_input to verify command processing
    mock_process_input = mocker.MagicMock()
    cli_instance.process_input = mock_process_input  # type: ignore

    # Set up shell mode for first input
    cli_instance.mode = CLIMode.SHELL

    # Run the interactive loop
    cli_instance.run_interactive_loop()

    # Verify execute_command was called with "ls"
    mock_execute.assert_called_once_with("ls")

    # Verify mode was reset to NORMAL after command execution
    assert mock_set_mode.call_args_list[-1][0][0] == CLIMode.NORMAL

    # Verify process_input was called with formatted shell output
    assert mock_process_input.call_count == 1
    args = mock_process_input.call_args[0][0]
    assert "Command:" in args
    assert "$ ls" in args
    assert "Output:" in args


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
