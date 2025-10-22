"""Tests for the execute_command tool."""

from io import StringIO
from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from simple_agent.tools.exec import execute_command


def test_execute_command() -> None:
    """Test the execute_command function."""
    # Test successful command
    stdout, stderr, return_code = execute_command("echo 'Hello, world!'")
    assert stdout.strip() == "Hello, world!"
    assert stderr == ""
    assert return_code == 0

    # Test command with error
    stdout, stderr, return_code = execute_command("some_invalid_command")
    assert stdout == ""
    assert "not found" in stderr
    assert return_code != 0

    # Test command with both stdout and stderr
    stdout, stderr, return_code = execute_command("echo 'out' && echo 'err' >&2")
    assert "out" in stdout
    assert "err" in stderr
    assert return_code == 0


def test_execute_command_exception(mocker: MockerFixture) -> None:
    """Test the execute_command function with an exception."""
    # Test with a command that causes a subprocess.Popen error
    mocker.patch("subprocess.Popen", side_effect=Exception("Test exception"))
    stdout, stderr, return_code = execute_command("anything")
    assert stdout == ""
    assert stderr == "Test exception"
    assert return_code == 1


def test_execute_command_remaining_output(mocker: MockerFixture) -> None:
    """Test reading remaining output after process completes.

    This test specifically targets reading from stdout and stderr after a process has finished.
    """
    from rich.padding import Padding

    # Create a mock process
    mock_process = MagicMock()
    mock_process.poll.return_value = 0  # Process has finished
    mock_process.returncode = 0

    # Create mock stdout and stderr with content
    mock_stdout = StringIO("remaining stdout line\n")
    mock_stderr = StringIO("remaining stderr line\n")

    # Setup process to return these streams
    mock_process.stdout = mock_stdout
    mock_process.stderr = mock_stderr

    # Mock select to simulate no initial output (go straight to process completed)
    mock_select = mocker.patch("simple_agent.tools.exec.execute_command.select")
    mock_select.return_value = ([], None, None)

    # Mock Popen to return our mock process
    mocker.patch("subprocess.Popen", return_value=mock_process)

    # Mock console.print
    mock_print = mocker.patch("simple_agent.tools.exec.execute_command.console.print")

    # Call execute_command
    stdout, stderr, return_code = execute_command("test_command")

    # Verify the function read the remaining output from stdout and stderr
    assert "remaining stdout line" in stdout
    assert "remaining stderr line" in stderr

    # Verify console.print was called with the appropriate content
    assert mock_print.call_count >= 3  # At least for stdout, stderr and completion

    # Find calls with Padding objects and check their content
    padding_calls = [
        call
        for call in mock_print.call_args_list
        if len(call[0]) > 0 and isinstance(call[0][0], Padding)
    ]

    # Verify stdout was printed
    stdout_found = any(
        "[dim]remaining stdout line[/dim]" in str(call[0][0].renderable)
        for call in padding_calls
    )
    assert stdout_found, "Expected stdout line not found in console.print calls"

    # Verify stderr was printed
    stderr_found = any(
        "[red]remaining stderr line[/red]" in str(call[0][0].renderable)
        for call in padding_calls
    )
    assert stderr_found, "Expected stderr line not found in console.print calls"

    # Verify completion message was printed
    completion_found = any(
        "Command completed:" in str(call[0][0].renderable) for call in padding_calls
    )
    assert (
        completion_found
    ), "Expected completion message not found in console.print calls"
