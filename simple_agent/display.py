"""Display utilities for standardized output formatting."""

from typing import Any

from prompt_toolkit import prompt
from prompt_toolkit.formatted_text import HTML
from rich.console import Console
from rich.traceback import Traceback

# Create a shared Console instance for all output
console = Console()


def display_response(message: str, status: str, next_action: str | None = None) -> None:
    """Display formatted agent response based on status.

    Args:
        message: Main response message
        status: Response status (COMPLETE, CONTINUE, ASK)
        next_action: Optional follow-up action or question
    """
    console.print(message)

    if status == "CONTINUE" and next_action:
        console.print(f"[bold blue]Next:[/bold blue] {next_action}")
    elif status == "ASK" and next_action:
        console.print(f"[bold yellow]Question:[/bold yellow] {next_action}")


def display_error(message: str, err: Exception | None = None) -> None:
    """Display formatted error message with optional exception details.

    Args:
        message: Human-readable error message
        err: Optional exception for display
    """
    # Display the primary error message
    console.print(f"[bold red]Error:[/bold red] {message}")

    # Display exception details if provided
    if err:
        console.print(
            Traceback.from_exception(
                type(err),
                err,
                err.__traceback__,
                show_locals=False,
                width=100,
                extra_lines=3,
                theme=None,
                word_wrap=True,
            )
        )


def display_warning(message: str, err: Exception | None = None) -> None:
    """Display formatted warning message with optional exception details.

    Args:
        message: Human-readable warning message
        err: Optional exception for display
    """
    # Display the primary warning message
    console.print(f"[bold yellow]Warning:[/bold yellow] {message}")

    # Display exception details if provided (with different styling from errors)
    if err:
        console.print(
            Traceback.from_exception(
                type(err),
                err,
                err.__traceback__,
                show_locals=False,
                width=100,
                extra_lines=3,
                theme=None,
                word_wrap=True,
            )
        )


def display_info(message: str) -> None:
    """Display formatted information message.

    Args:
        message: Information text to display
    """
    console.print(f"[blue]Info:[/blue] {message}")


def display_command(command: str) -> None:
    """Display formatted shell command.

    Args:
        command: The shell command to be displayed
    """
    console.print(f"[cyan]$ {command}[/cyan]")


def display_command_output(output: str) -> None:
    """Display shell command output.

    Args:
        output: The output text from a shell command
    """
    console.print(output)


def get_confirmation(message: str, default: bool = True) -> bool:
    """Get user confirmation with standardized formatting.

    Args:
        message: Question to ask the user
        default: Default value if user hits Enter

    Returns:
        True if confirmed, False otherwise
    """
    default_text = "[Y/n]" if default else "[y/N]"
    result = prompt(
        HTML(f"<ansiblue>{message}</ansiblue> <ansiyellow>{default_text}</ansiyellow> ")
    )

    if not result:
        return default
    return result.lower() in ["y", "yes"]


def display_success(message: str) -> None:
    """Display formatted success message.

    Args:
        message: Success message to display
    """
    console.print(f"[green]Success:[/green] {message}")


def print_tool_call(tool_name: str, **args: Any) -> None:
    """Print standardized tool execution announcement.

    Args:
        tool_name: Name of the tool being executed
        **args: Tool arguments
    """
    # Format args for display
    args_str = ", ".join(f"{k}={repr(v)}" for k, v in args.items())
    console.print(f"[bold]Executing[/bold] [cyan]{tool_name}[/cyan]({args_str})")


def print_tool_result(tool_name: str, result: Any) -> None:
    """Print standardized tool execution result.

    Args:
        tool_name: Name of the tool that was executed
        result: Result of the tool execution
    """
    if isinstance(result, bool):
        status = "[green]succeeded[/green]" if result else "[yellow]cancelled[/yellow]"
        console.print(f"Tool [cyan]{tool_name}[/cyan] {status}")
    elif isinstance(result, list | dict) and result:
        # For collections, show the count of items
        count = len(result)
        console.print(f"Tool [cyan]{tool_name}[/cyan] returned {count} item(s)")
    else:
        # For other non-empty results, indicate success
        console.print(f"Tool [cyan]{tool_name}[/cyan] completed successfully")
