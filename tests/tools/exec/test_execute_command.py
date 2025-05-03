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
    # Create a mock process
    mock_process = MagicMock()
    mock_process.poll.return_value = 0  # Process has finished

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

    # Mock sys.stdout and sys.stderr
    mock_sys_stdout = mocker.patch("sys.stdout.write")
    mock_sys_stderr = mocker.patch("sys.stderr.write")

    # Call execute_command
    stdout, stderr, return_code = execute_command("test_command")

    # Verify the function read the remaining output from stdout and stderr
    assert "remaining stdout line" in stdout
    assert "remaining stderr line" in stderr

    # Verify that the content was written to sys.stdout and sys.stderr
    mock_sys_stdout.assert_called_with("remaining stdout line\n")
    mock_sys_stderr.assert_called_with("remaining stderr line\n")
