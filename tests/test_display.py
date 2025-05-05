"""Tests for the display utilities module."""

from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console
from rich.syntax import Syntax
from rich.traceback import Traceback

from simple_agent.display import (
    console,
    display_command,
    display_command_output,
    display_error,
    display_info,
    display_response,
    display_success,
    display_warning,
    get_confirmation,
    print_tool_call,
    print_tool_result,
)


def test_display_console_created():
    """Test that the console is created as a Rich Console instance."""
    assert isinstance(console, Console)


@patch("simple_agent.display.console.print")
def test_display_response_complete(mock_print):
    """Test display_response with COMPLETE status."""
    display_response("Test message", "COMPLETE", None)
    
    # Should just print the message with no extra formatting
    mock_print.assert_called_once_with("Test message")


@patch("simple_agent.display.console.print")
def test_display_response_continue(mock_print):
    """Test display_response with CONTINUE status."""
    display_response("Working on it", "CONTINUE", "I'll check something else")
    
    # Should print message and next action separately
    assert mock_print.call_count == 2
    mock_print.assert_any_call("Working on it")
    mock_print.assert_any_call("[bold blue]Next:[/bold blue] I'll check something else")


@patch("simple_agent.display.console.print")
def test_display_response_ask(mock_print):
    """Test display_response with ASK status."""
    display_response("Found multiple options", "ASK", "Which option do you prefer?")
    
    # Should print message and question separately
    assert mock_print.call_count == 2
    mock_print.assert_any_call("Found multiple options")
    mock_print.assert_any_call("[bold yellow]Question:[/bold yellow] Which option do you prefer?")


@patch("simple_agent.display.console.print")
def test_display_response_no_next_action(mock_print):
    """Test display_response with CONTINUE status but no next_action."""
    display_response("Working on it", "CONTINUE", None)
    
    # Should only print the message
    mock_print.assert_called_once_with("Working on it")


@patch("simple_agent.display.console.print")
def test_display_error_without_exception(mock_print):
    """Test display_error without an exception."""
    display_error("Something went wrong")
    
    # Should print error message with formatting
    mock_print.assert_called_once_with("[bold red]Error:[/bold red] Something went wrong")


@patch("simple_agent.display.console.print")
def test_display_error_with_exception(mock_print):
    """Test display_error with an exception."""
    error = ValueError("Invalid value")
    
    display_error("Something went wrong", error)
    
    # Should print error message and traceback
    assert mock_print.call_count == 2
    mock_print.assert_any_call("[bold red]Error:[/bold red] Something went wrong")
    
    # Second call should be with a Traceback object
    second_call_args = mock_print.call_args_list[1][0][0]
    assert isinstance(second_call_args, Traceback)


@patch("simple_agent.display.console.print")
def test_display_warning_without_exception(mock_print):
    """Test display_warning without an exception."""
    display_warning("Potentially problematic")
    
    # Should print warning message with formatting
    mock_print.assert_called_once_with("[bold yellow]Warning:[/bold yellow] Potentially problematic")


@patch("simple_agent.display.console.print")
def test_display_warning_with_exception(mock_print):
    """Test display_warning with an exception."""
    error = ValueError("Invalid value")
    
    display_warning("Potentially problematic", error)
    
    # Should print warning message and traceback
    assert mock_print.call_count == 2
    mock_print.assert_any_call("[bold yellow]Warning:[/bold yellow] Potentially problematic")
    
    # Second call should be with a Traceback object
    second_call_args = mock_print.call_args_list[1][0][0]
    assert isinstance(second_call_args, Traceback)


@patch("simple_agent.display.console.print")
def test_display_info(mock_print):
    """Test display_info."""
    display_info("Processing request")
    
    # Should print info message with formatting
    mock_print.assert_called_once_with("[blue]Info:[/blue] Processing request")


@patch("simple_agent.display.console.print")
def test_display_command(mock_print):
    """Test display_command."""
    display_command("ls -la")
    
    # Should print command with formatting
    mock_print.assert_called_once_with("[cyan]$ ls -la[/cyan]")


@patch("simple_agent.display.console.print")
def test_display_command_output(mock_print):
    """Test display_command_output."""
    display_command_output("file1.txt\nfile2.txt")
    
    # Should print output as is
    mock_print.assert_called_once_with("file1.txt\nfile2.txt")


@patch("simple_agent.display.prompt")
def test_get_confirmation_default_yes(mock_prompt):
    """Test get_confirmation with default=True."""
    # Empty response (hitting Enter)
    mock_prompt.return_value = ""
    
    result = get_confirmation("Proceed?")
    
    # Should return True for empty input with default=True
    assert result is True
    
    # Check that prompt was called
    mock_prompt.assert_called_once()


@patch("simple_agent.display.prompt")
def test_get_confirmation_default_no(mock_prompt):
    """Test get_confirmation with default=False."""
    # Empty response (hitting Enter)
    mock_prompt.return_value = ""
    
    result = get_confirmation("Proceed?", default=False)
    
    # Should return False for empty input with default=False
    assert result is False
    
    # Verify prompt was called
    mock_prompt.assert_called_once()


@patch("simple_agent.display.prompt")
def test_get_confirmation_explicit_yes(mock_prompt):
    """Test get_confirmation with explicit yes responses."""
    for response in ["y", "Y", "yes", "YES", "Yes"]:
        mock_prompt.return_value = response
        result = get_confirmation("Proceed?")
        assert result is True


@patch("simple_agent.display.prompt")
def test_get_confirmation_explicit_no(mock_prompt):
    """Test get_confirmation with explicit no responses."""
    for response in ["n", "N", "no", "NO", "No"]:
        mock_prompt.return_value = response
        result = get_confirmation("Proceed?")
        assert result is False


@patch("simple_agent.display.console.print")
def test_display_success(mock_print):
    """Test display_success."""
    display_success("Operation completed")
    
    # Should print success message with formatting
    mock_print.assert_called_once_with("[green]Success:[/green] Operation completed")


@patch("simple_agent.display.console.print")
def test_print_tool_call(mock_print):
    """Test print_tool_call."""
    # Test with simple arguments
    print_tool_call("read_file", file_path="example.txt")
    
    # Should print formatted tool call
    call_args = mock_print.call_args[0][0]
    assert "[bold]Executing[/bold]" in call_args
    assert "[cyan]read_file[/cyan]" in call_args
    assert "file_path='example.txt'" in call_args
    
    # Test with multiple arguments
    mock_print.reset_mock()
    print_tool_call("write_file", file_path="example.txt", content="Example content")
    
    call_args = mock_print.call_args[0][0]
    assert "[bold]Executing[/bold]" in call_args
    assert "[cyan]write_file[/cyan]" in call_args
    assert "file_path='example.txt'" in call_args
    assert "content='Example content'" in call_args


@patch("simple_agent.display.console.print")
def test_print_tool_result_boolean(mock_print):
    """Test print_tool_result with boolean results."""
    # Test with True result
    print_tool_result("write_file", True)
    call_args = mock_print.call_args[0][0]
    assert "Tool [cyan]write_file[/cyan]" in call_args
    assert "[green]succeeded[/green]" in call_args
    
    # Test with False result
    mock_print.reset_mock()
    print_tool_result("write_file", False)
    call_args = mock_print.call_args[0][0]
    assert "Tool [cyan]write_file[/cyan]" in call_args
    assert "[yellow]cancelled[/yellow]" in call_args


@patch("simple_agent.display.console.print")
def test_print_tool_result_collection(mock_print):
    """Test print_tool_result with collection results."""
    # Test with list result
    print_tool_result("glob_files", ["file1.txt", "file2.txt"])
    call_args = mock_print.call_args[0][0]
    assert "Tool [cyan]glob_files[/cyan]" in call_args
    assert "returned 2 item(s)" in call_args
    
    # Test with dict result
    mock_print.reset_mock()
    print_tool_result("list_directory", {"files": ["file1.txt"], "dirs": ["dir1"]})
    call_args = mock_print.call_args[0][0]
    assert "Tool [cyan]list_directory[/cyan]" in call_args
    assert "returned 2 item(s)" in call_args
    
    # Test with empty collection
    mock_print.reset_mock()
    print_tool_result("glob_files", [])
    call_args = mock_print.call_args[0][0]
    assert "Tool [cyan]glob_files[/cyan]" in call_args
    assert "completed successfully" in call_args


@patch("simple_agent.display.console.print")
def test_print_tool_result_other(mock_print):
    """Test print_tool_result with other result types."""
    # Test with string result
    print_tool_result("get_version", "1.0.0")
    call_args = mock_print.call_args[0][0]
    assert "Tool [cyan]get_version[/cyan]" in call_args
    assert "completed successfully" in call_args
    
    # Test with None result
    mock_print.reset_mock()
    print_tool_result("some_tool", None)
    call_args = mock_print.call_args[0][0]
    assert "Tool [cyan]some_tool[/cyan]" in call_args
    assert "completed successfully" in call_args