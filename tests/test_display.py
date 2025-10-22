"""Tests for the display utilities module."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockerFixture
from rich.console import Console
from rich.traceback import Traceback

from simple_agent.display import (
    clean_path,
    console,
    display_command,
    display_error,
    display_exit,
    display_info,
    display_status_message,
    display_warning,
    format_tool_args,
    get_confirmation,
    print_tool_call,
    print_tool_result,
)


def test_display_console_created() -> None:
    """Test that the console is created as a Rich Console instance."""
    assert isinstance(console, Console)


@patch("simple_agent.display.console.print")
def test_display_error_without_exception(mock_print: MagicMock) -> None:
    """Test display_error without an exception."""
    from rich.padding import Padding

    display_error("Something went wrong")

    # Should call console.print with error message formatting
    mock_print.assert_called_once()
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    assert call_args.renderable == "[bold red]Error:[/bold red] Something went wrong"


@patch("simple_agent.live_console.live_display", None)  # Simulate no live display
@patch("simple_agent.display.console.print")
def test_display_error_with_exception(mock_print: MagicMock) -> None:
    """Test display_error with an exception."""
    from rich.padding import Padding

    error = ValueError("Invalid value")

    display_error("Something went wrong", error)

    # Should print error message and traceback
    assert mock_print.call_count == 2

    # First call should be the error message with padding
    first_call_args = mock_print.call_args_list[0][0][0]
    assert isinstance(first_call_args, Padding)
    assert (
        first_call_args.renderable == "[bold red]Error:[/bold red] Something went wrong"
    )

    # Second call should be the traceback
    second_call_args = mock_print.call_args_list[1][0][0]
    assert isinstance(second_call_args, Traceback)


@patch("simple_agent.display.console.print")
def test_display_warning_without_exception(mock_print: MagicMock) -> None:
    """Test display_warning without an exception."""
    from rich.padding import Padding

    display_warning("Potentially problematic")

    # Should print warning message
    mock_print.assert_called_once()
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    assert (
        call_args.renderable
        == "[bold yellow]Warning:[/bold yellow] Potentially problematic"
    )


@patch("simple_agent.display.console.print")
def test_display_warning_with_exception(mock_print: MagicMock) -> None:
    """Test display_warning with an exception."""
    from rich.padding import Padding

    error = ValueError("Invalid value")

    display_warning("Potentially problematic", error)

    # Should print warning message and error details
    assert mock_print.call_count == 2
    first_call_args = mock_print.call_args_list[0][0][0]
    assert isinstance(first_call_args, Padding)
    assert (
        first_call_args.renderable
        == "[bold yellow]Warning:[/bold yellow] Potentially problematic"
    )

    second_call_args = mock_print.call_args_list[1][0][0]
    assert isinstance(second_call_args, Padding)
    assert (
        second_call_args.renderable
        == "[dim]Exception: ValueError 'Invalid value'[/dim]"
    )


@patch("simple_agent.display.console.print")
def test_display_info(mock_print: MagicMock) -> None:
    """Test display_info."""
    from rich.padding import Padding

    display_info("Processing request")

    # Should print info message
    mock_print.assert_called_once()
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    assert call_args.renderable == "Processing request"


@patch("simple_agent.display.console.print")
def test_display_command(mock_print: MagicMock) -> None:
    """Test display_command."""
    from rich.padding import Padding

    display_command("ls -la")

    # Should print formatted command
    mock_print.assert_called_once()
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    assert call_args.renderable == "[cyan]$ ls -la[/cyan]"


@patch("simple_agent.display.live_confirmation")
def test_get_confirmation_default_yes(mock_confirm: MagicMock) -> None:
    """Test get_confirmation with default=True."""
    # Mock the return value
    mock_confirm.return_value = True

    result = get_confirmation("Proceed?")

    # Should return True
    assert result is True

    # Verify live_confirmation was called with the right parameters
    mock_confirm.assert_called_once_with("Proceed?", True)


@patch("simple_agent.display.live_confirmation")
def test_get_confirmation_default_no(mock_confirm: MagicMock) -> None:
    """Test get_confirmation with default=False."""
    # Mock the return value
    mock_confirm.return_value = False

    result = get_confirmation("Proceed?", default=False)

    # Should return False
    assert result is False

    # Verify live_confirmation was called with the right parameters
    mock_confirm.assert_called_once_with("Proceed?", False)


@patch("simple_agent.display.live_confirmation")
def test_get_confirmation_explicit_yes(mock_confirm: MagicMock) -> None:
    """Test get_confirmation with explicit yes response."""
    # Mock the return value
    mock_confirm.return_value = True

    result = get_confirmation("Proceed?")

    # Should return True
    assert result is True

    # Verify live_confirmation was called
    mock_confirm.assert_called_once()


@patch("simple_agent.display.live_confirmation")
def test_get_confirmation_explicit_no(mock_confirm: MagicMock) -> None:
    """Test get_confirmation with explicit no response."""
    # Mock the return value
    mock_confirm.return_value = False

    result = get_confirmation("Proceed?")

    # Should return False
    assert result is False

    # Verify live_confirmation was called
    mock_confirm.assert_called_once()


@patch("simple_agent.display.console.print")
def test_display_exit(mock_print: MagicMock) -> None:
    """Test display_exit."""
    from rich.padding import Padding

    display_exit("User interrupted")

    # Should print exit message with formatting and padding
    mock_print.assert_called_once()
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    assert call_args.renderable == "[bold blue]Exiting:[/bold blue] User interrupted"


@patch("simple_agent.display.console.print")
def test_print_tool_call(mock_print: MagicMock) -> None:
    """Test print_tool_call."""
    from rich.padding import Padding

    # Test with simple arguments
    print_tool_call("read_file", file_path="example.txt")

    # Should print formatted tool call
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    renderable_str = str(call_args.renderable)
    assert "[cyan]read_file[/cyan]" in renderable_str
    assert "file_path='example.txt'" in renderable_str

    # Test with multiple arguments
    mock_print.reset_mock()
    print_tool_call("write_file", file_path="example.txt", content="Example content")

    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    renderable_str = str(call_args.renderable)
    assert "[cyan]write_file[/cyan]" in renderable_str
    assert "file_path='example.txt'" in renderable_str
    assert "content='Example content'" in renderable_str


def test_print_tool_call_with_mocked_format(
    monkeypatch: pytest.MonkeyPatch, mocker: MockerFixture
) -> None:
    """Test print_tool_call with mocked format_tool_args."""
    from rich.padding import Padding

    # Mock console.print
    mock_print = mocker.patch("simple_agent.display.console.print")

    # Mock format_tool_args to return a known string for testing
    mock_format_args = mocker.patch("simple_agent.display.format_tool_args")
    mock_format_args.return_value = "arg1=value1, arg2=value2"

    # Mock the current working directory
    test_cwd = Path("/home/user/project")
    monkeypatch.setattr(Path, "cwd", lambda: test_cwd)

    # Test with simple tool call using keyword arguments
    print_tool_call("test_tool", arg1="value1", arg2="value2")

    # Verify that console.print was called with a Padding containing the tool name and formatted args
    mock_print.assert_called_once()
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    assert "test_tool" in str(call_args.renderable)

    # Reset mocks
    mock_print.reset_mock()
    mock_format_args.reset_mock()

    # Set up mock for second test
    mock_format_args.return_value = "file.txt"

    # Test with file_paths keyword argument
    print_tool_call("read_files", file_paths=[str(test_cwd / "file.txt")])
    mock_print.assert_called_once()
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    assert "read_files" in str(call_args.renderable)


@patch("simple_agent.display.console.print")
def test_print_tool_result(mock_print: MagicMock) -> None:
    """Test print_tool_result with message."""
    from rich.padding import Padding

    # Test with success message
    print_tool_result("write_file", "File successfully written")
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    renderable_str = str(call_args.renderable)
    assert "[cyan]write_file[/cyan]" in renderable_str
    assert "File successfully written" in renderable_str

    # Test with error message
    mock_print.reset_mock()
    print_tool_result("write_file", "Failed to write file")
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    renderable_str = str(call_args.renderable)
    assert "[cyan]write_file[/cyan]" in renderable_str
    assert "Failed to write file" in renderable_str

    # Test with file count message
    mock_print.reset_mock()
    print_tool_result("glob_files", "Found 2 files matching pattern '*.txt'")
    call_args = mock_print.call_args[0][0]
    assert isinstance(call_args, Padding)
    renderable_str = str(call_args.renderable)
    assert "[cyan]glob_files[/cyan]" in renderable_str
    assert "Found 2 files matching pattern '*.txt'" in renderable_str


def test_clean_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the clean_path function."""
    # Mock the current working directory
    test_cwd = Path("/home/user/project")
    monkeypatch.setattr(Path, "cwd", lambda: test_cwd)

    # Test with path under CWD
    cwd_path = str(test_cwd / "file.txt")
    assert clean_path(cwd_path) == "file.txt"

    # Test with path in subdirectory under CWD
    subdir_path = str(test_cwd / "subdir" / "file.txt")
    assert clean_path(subdir_path) == "subdir/file.txt"

    # Test with CWD itself
    assert clean_path(str(test_cwd)) == "."

    # Test with path outside CWD
    outside_path = "/tmp/file.txt"
    assert clean_path(outside_path) == outside_path

    # Test with relative path (should remain unchanged)
    relative_path = "relative/path.txt"
    assert clean_path(relative_path) == relative_path


def test_format_tool_args(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the format_tool_args function."""
    # Mock the current working directory
    test_cwd = Path("/home/user/project")
    monkeypatch.setattr(Path, "cwd", lambda: test_cwd)

    # Test with string arguments
    path = str(test_cwd / "file.txt")
    assert format_tool_args(path) == "'file.txt'"

    # Test with multiple string arguments
    path2 = str(test_cwd / "another.txt")
    assert format_tool_args(path, path2) == "'file.txt', 'another.txt'"

    # Test with non-string arguments
    assert format_tool_args(123) == "123"
    assert format_tool_args(path, 123, True) == "'file.txt', 123, True"

    # Test with list of strings
    path_list = [str(test_cwd / "file1.txt"), str(test_cwd / "file2.txt")]
    result = format_tool_args(path_list)
    assert "'file1.txt'" in result
    assert "'file2.txt'" in result

    # Test with empty list
    assert format_tool_args([]) == ""

    # Test with list of non-strings
    result = format_tool_args([1, 2, 3])
    assert "<list>" in result  # Implementation changed to show type instead of value

    # Test with keyword arguments
    result = format_tool_args(file=path, num=42, flag=True)
    assert "file='file.txt'" in result
    assert "num=42" in result
    assert "flag=True" in result

    # Test with other list keyword arguments
    result = format_tool_args(paths=path_list)
    assert "paths=[" in result
    assert "'file1.txt'" in result
    assert "'file2.txt'" in result

    # Test combined positional and keyword arguments
    result = format_tool_args(path, pattern="*.py", file_paths=path_list)
    assert "'file.txt'" in result
    assert "pattern='*.py'" in result
    assert "'file1.txt', 'file2.txt'" in result


def test_display_status_message_with_cost() -> None:
    """Test display_status_message with cost information."""
    # Test with tokens, elapsed time, and cost
    result = display_status_message(100, 50, 2.5, 0.0025)
    assert "Tokens: 100 sent / 50 recv" in result
    assert "Time: 2s" in result
    assert "Cost: $0.0025" in result

    # Test with different cost value
    result = display_status_message(500, 200, 10.8, 0.0125)
    assert "Tokens: 500 sent / 200 recv" in result
    assert "Time: 10s" in result
    assert "Cost: $0.0125" in result

    # Test with larger cost value
    result = display_status_message(5000, 3000, 25.2, 0.1500)
    assert "Tokens: 5,000 sent / 3,000 recv" in result
    assert "Time: 25s" in result
    assert "Cost: $0.1500" in result


def test_display_status_message_without_cost() -> None:
    """Test display_status_message without cost information."""
    # Test with tokens and elapsed time, but no cost
    result = display_status_message(100, 50, 2.5)
    assert "Tokens: 100 sent / 50 recv" in result
    assert "Time: 2s" in result
    assert "Cost:" not in result  # Cost should not be present

    # Test with just tokens (no time or cost)
    result = display_status_message(200, 100)
    assert "Tokens: 200 sent / 100 recv" in result
    assert "Time:" not in result
    assert "Cost:" not in result


def test_display_status_message_with_minutes() -> None:
    """Test display_status_message with time in minutes."""
    # Test with time in minutes format
    result = display_status_message(1000, 500, 65, 0.0075)
    assert "Tokens: 1,000 sent / 500 recv" in result
    assert "Time: 1m 5s" in result
    assert "Cost: $0.0075" in result

    # Test with longer time
    result = display_status_message(2000, 1000, 125, 0.0150)
    assert "Tokens: 2,000 sent / 1,000 recv" in result
    assert "Time: 2m 5s" in result
    assert "Cost: $0.0150" in result
