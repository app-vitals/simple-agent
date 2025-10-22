"""Tests for the live_console module."""

from unittest.mock import MagicMock, patch

import pytest
from pytest_mock import MockerFixture
from rich.console import Console
from rich.live import Live

from simple_agent.live_console import (
    console,
    live_confirmation,
    live_context,
    set_stage_message,
)


def test_console_created() -> None:
    """Test that the console is created as a Rich Console instance."""
    assert isinstance(console, Console)


def test_set_stage_message() -> None:
    """Test the set_stage_message function."""
    # Set a stage message
    set_stage_message("Testing")
    from simple_agent.live_console import current_stage

    assert current_stage == "Testing"

    # Set another stage message
    set_stage_message("Processing")
    from simple_agent.live_console import current_stage

    assert current_stage == "Processing"


def test_live_context(mocker: MockerFixture) -> None:
    """Test the live_context context manager."""
    # Mock the Live class
    mock_live = mocker.patch("simple_agent.live_console.Live")
    mock_live_instance = mock_live.return_value

    # Mock threading.Thread to avoid actually starting a thread
    mock_thread = mocker.patch("threading.Thread")
    mock_thread_instance = MagicMock()
    mock_thread.return_value = mock_thread_instance

    # Create a simple status callback
    def status_callback() -> str:
        return "Status: testing"

    # Use the context manager
    with live_context(status_callback=status_callback):
        # Verify that Live was created and started
        assert mock_live.called
        mock_live_instance.start.assert_called_once()

        # Verify thread was created and started
        assert mock_thread.called
        mock_thread_instance.start.assert_called_once()

    # Verify that Live was stopped after exiting the context
    mock_live_instance.stop.assert_called_once()


def test_live_context_without_callback(mocker: MockerFixture) -> None:
    """Test the live_context context manager without a status callback."""
    # Mock the Live class
    mock_live = mocker.patch("simple_agent.live_console.Live")
    mock_live_instance = mock_live.return_value

    # No need to mock threading.Thread since no callback means no thread

    # Use the context manager without a status callback
    with live_context():
        # Verify that Live was created and started
        assert mock_live.called
        mock_live_instance.start.assert_called_once()

    # Verify that Live was stopped after exiting the context
    mock_live_instance.stop.assert_called_once()


def test_live_context_exception_handling(mocker: MockerFixture) -> None:
    """Test that the live_context handles exceptions properly."""
    # Mock the Live class
    mock_live = mocker.patch("simple_agent.live_console.Live")
    mock_live_instance = mock_live.return_value

    # Use the context manager with an exception
    try:
        with live_context():
            raise ValueError("Test exception")
    except ValueError:
        pass

    # Verify that Live was stopped even though an exception was raised
    mock_live_instance.stop.assert_called_once()


@patch("builtins.input")
@patch("simple_agent.live_console.live_display", None)
def test_live_confirmation_without_live_display(mock_input: MagicMock) -> None:
    """Test live_confirmation when live_display is not available."""
    # Set up mock input
    mock_input.return_value = ""

    # Call live_confirmation with default=True
    result = live_confirmation("Test message", default=True)

    # Verify input was called and True was returned for empty input
    mock_input.assert_called_once()
    assert result is True

    # Reset mock and test with default=False
    mock_input.reset_mock()
    mock_input.return_value = ""

    result = live_confirmation("Test message", default=False)

    # Verify input was called and False was returned for empty input
    mock_input.assert_called_once()
    assert result is False

    # Test explicit responses
    for response, expected in [
        ("y", True),
        ("Y", True),
        ("yes", True),
        ("YES", True),
        ("n", False),
        ("N", False),
        ("no", False),
        ("NO", False),
    ]:
        mock_input.reset_mock()
        mock_input.return_value = response

        result = live_confirmation("Test message")
        assert result is expected


@patch("builtins.input")
def test_live_confirmation_with_live_display(
    mock_input: MagicMock, mocker: MockerFixture
) -> None:
    """Test live_confirmation when live_display is available."""
    # Mock live_display
    mock_live = MagicMock(spec=Live)

    # Patch live_display
    mocker.patch("simple_agent.live_console.live_display", mock_live)

    # Mock console.print
    mock_console_print = mocker.patch("simple_agent.live_console.console.print")

    # Set up mock input
    mock_input.return_value = "y"

    # Call live_confirmation
    result = live_confirmation("Test message")

    # Verify stop and start were called
    mock_live.stop.assert_called_once()
    mock_live.start.assert_called_once()

    # Verify input was called and result is True
    mock_input.assert_called_once()
    assert result is True

    # Verify console.print was called 3 times (newline before, confirmation result, newline after)
    assert mock_console_print.call_count == 3


def test_live_confirmation_exception_handling(mocker: MockerFixture) -> None:
    """Test live_confirmation handles exceptions properly."""
    # Mock live_display
    mock_live = mocker.patch("simple_agent.live_console.live_display")

    # Mock input to raise an exception
    mock_input = mocker.patch("builtins.input")
    mock_input.side_effect = ValueError("Test exception")

    # No need to mock the is_active property since we updated the code

    # Call live_confirmation and expect the exception to be re-raised
    with pytest.raises(ValueError):
        live_confirmation("Test message")

    # Verify the live display was stopped and restarted
    mock_live.stop.assert_called_once()
    mock_live.start.assert_called_once()
