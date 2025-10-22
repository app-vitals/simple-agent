"""Live console display for dynamic updates during processing."""

import contextlib
import threading
import time
from collections.abc import Callable, Generator

from rich.box import MINIMAL
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

# Create a shared Console instance for all output
console = Console()

# Create a shared Live display instance for dynamic updates
live_display: Live | None = None

# Current processing stage message
current_stage = "Processing..."


@contextlib.contextmanager
def live_context(
    status_callback: Callable[[], str] | None = None, update_interval: float = 0.25
) -> Generator[Live, None, None]:
    """Context manager for live display updates.

    Args:
        status_callback: Optional callback function that returns status text
        update_interval: Time between status updates in seconds

    Yields:
        Rich Live context for dynamic updates
    """
    global live_display

    # Create a new Live display with just the status line
    live = Live(
        Panel(
            "[blue]Processing...[/blue] • Starting",
            box=MINIMAL,
            padding=(0, 1),
            expand=False,
        ),
        console=console,
        refresh_per_second=8,
        transient=False,
    )

    # Set up status updater thread if a callback is provided
    stop_event = threading.Event()
    status_thread = None

    if status_callback is not None:

        def update_status() -> None:
            while not stop_event.is_set():
                if live_display:
                    try:
                        # Get current status from callback
                        current_status = status_callback()

                        # Format the status line
                        status_line = f"[blue]{current_stage}[/blue] • {current_status}"

                        # Update the live display with just the status
                        live_display.update(
                            Panel(
                                status_line,
                                box=MINIMAL,
                                padding=(0, 1),
                                expand=False,
                            )
                        )
                    except Exception:
                        # Ignore any errors in the update thread
                        pass

                # Sleep for the update interval
                time.sleep(update_interval)

        # Create and start the status update thread
        status_thread = threading.Thread(target=update_status, daemon=True)

    try:
        # Start the live display
        live.start()
        live_display = live

        # Start the status update thread if it exists
        if status_thread:
            status_thread.start()

        yield live
    finally:
        # Signal the status thread to stop
        stop_event.set()

        # Wait for the status thread to finish if it exists
        if status_thread and status_thread.is_alive():
            status_thread.join(timeout=0.5)  # Wait up to 0.5s for thread to end

        # Ensure the live display is stopped
        live.stop()
        live_display = None


def set_stage_message(message: str) -> None:
    """Set the current processing stage message.

    Args:
        message: The stage message to display
    """
    global current_stage
    current_stage = message


def live_confirmation(message: str, default: bool = True) -> bool:
    """Get user confirmation within the live display.

    Args:
        message: The confirmation message to display
        default: Default response if user just presses Enter

    Returns:
        True if confirmed, False if denied
    """
    if live_display is None:
        # Fallback to standard input if live display isn't available
        default_text = "Y/n" if default else "y/N"
        response = input(f"  Confirm {message} [{default_text}] ")
        if not response:
            return default
        return response.lower() in ["y", "yes"]

    # No need to create this message since we're already formatting it for input/output
    # and it's not used elsewhere in the function

    # Temporarily stop the live display to get user input
    live_display.transient = True
    live_display.stop()

    # Add a newline before the confirmation prompt
    console.print()

    try:
        # Use a colored prompt for the confirmation
        # This uses ANSI escape codes for color since we're outside of Rich's rendering
        default_text = "Y/n" if default else "y/N"
        yellow_text = "\033[93m"  # ANSI bright yellow
        cyan_text = "\033[96m"  # ANSI bright cyan
        reset_text = "\033[0m"  # ANSI reset

        # Convert any Rich markup to ANSI colors
        formatted_message = message

        # Common color conversions
        formatted_message = formatted_message.replace("[cyan]", cyan_text)
        formatted_message = formatted_message.replace("[/cyan]", reset_text)
        formatted_message = formatted_message.replace("[blue]", "\033[94m")
        formatted_message = formatted_message.replace("[/blue]", reset_text)
        formatted_message = formatted_message.replace("[green]", "\033[92m")
        formatted_message = formatted_message.replace("[/green]", reset_text)
        formatted_message = formatted_message.replace("[red]", "\033[91m")
        formatted_message = formatted_message.replace("[/red]", reset_text)
        formatted_message = formatted_message.replace("[yellow]", "\033[93m")
        formatted_message = formatted_message.replace("[/yellow]", reset_text)

        # Style conversions
        formatted_message = formatted_message.replace("[bold]", "\033[1m")
        formatted_message = formatted_message.replace("[/bold]", reset_text)
        formatted_message = formatted_message.replace("[dim]", "\033[2m")
        formatted_message = formatted_message.replace("[/dim]", reset_text)
        formatted_message = formatted_message.replace("[italic]", "\033[3m")
        formatted_message = formatted_message.replace("[/italic]", reset_text)

        response = input(
            f"  {yellow_text}Confirm{reset_text} {formatted_message} {yellow_text}[{default_text}]{reset_text} "
        )

        # Process the response using a ternary operator
        result = default if not response else response.lower() in ["y", "yes"]

        # Display the user's choice
        choice_text = "Yes" if result else "No"
        confirmation_result = (
            f"[bold yellow]Confirm[/bold yellow] {message} [bold]→ {choice_text}[/bold]"
        )

        # Print the confirmation result with padding BEFORE restarting live display
        from rich.padding import Padding

        console.print(Padding(confirmation_result, (0, 0, 0, 2)))
        console.print()

        # Resume the live display after printing
        live_display.transient = False
        live_display.start()

        return result
    except Exception as e:
        # Make sure we restart the live display even if there's an error
        if live_display:
            # Use suppress to ignore any exceptions when trying to restart
            with contextlib.suppress(Exception):
                live_display.start()
        # Re-raise the exception
        raise e
