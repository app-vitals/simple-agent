"""Tests for the exec module."""

from pytest_mock import MockerFixture

from simple_agent.tools import exec


def test_execute_command() -> None:
    """Test the execute_command function."""
    # Test successful command
    stdout, stderr, return_code = exec.execute_command("echo 'Hello, world!'")
    assert stdout.strip() == "Hello, world!"
    assert stderr == ""
    assert return_code == 0

    # Test command with error
    stdout, stderr, return_code = exec.execute_command("some_invalid_command")
    assert stdout == ""
    assert "not found" in stderr
    assert return_code != 0

    # Test command with both stdout and stderr
    stdout, stderr, return_code = exec.execute_command("echo 'out' && echo 'err' >&2")
    assert "out" in stdout
    assert "err" in stderr
    assert return_code == 0


def test_execute_command_exception(mocker: MockerFixture) -> None:
    """Test the execute_command function with an exception."""
    # Test with a command that causes a subprocess.Popen error
    mocker.patch("subprocess.Popen", side_effect=Exception("Test exception"))
    stdout, stderr, return_code = exec.execute_command("anything")
    assert stdout == ""
    assert stderr == "Test exception"
    assert return_code == 1
