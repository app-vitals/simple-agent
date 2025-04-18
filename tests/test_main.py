"""Tests for the main module."""

import pytest
from pytest_mock import MockerFixture

from simple_agent.__main__ import main


def test_main_version(mocker: MockerFixture) -> None:
    """Test the main function with --version flag."""
    # Mock the arguments
    mocker.patch("sys.argv", ["simple-agent", "--version"])
    # Mock print to capture output
    mock_print = mocker.patch("builtins.print")

    main()
    mock_print.assert_called_once_with("simple-agent version 0.1.0")


def test_main_run_agent(mocker: MockerFixture) -> None:
    """Test the main function normal operation."""
    # Mock the arguments
    mocker.patch("sys.argv", ["simple-agent"])
    
    # Mock Agent class
    mock_agent = mocker.MagicMock()
    mock_agent_class = mocker.patch("simple_agent.__main__.Agent", return_value=mock_agent)
    
    # Run main
    main()
    
    # Verify Agent was instantiated and run was called
    mock_agent_class.assert_called_once()
    mock_agent.run.assert_called_once()


def test_main_keyboard_interrupt(mocker: MockerFixture) -> None:
    """Test the main function with keyboard interrupt."""
    # Mock the arguments
    mocker.patch("sys.argv", ["simple-agent"])
    
    # Mock Agent to raise KeyboardInterrupt
    mock_agent = mocker.MagicMock()
    mock_agent.run.side_effect = KeyboardInterrupt()
    mocker.patch("simple_agent.__main__.Agent", return_value=mock_agent)
    
    # Mock console and sys.exit
    mock_console = mocker.MagicMock()
    mocker.patch("simple_agent.__main__.Console", return_value=mock_console)
    mock_exit = mocker.patch("sys.exit")
    
    # Run main
    main()
    
    # Verify console output and exit code
    mock_console.print.assert_called_once_with("\n[yellow]Interrupted. Exiting.[/yellow]")
    mock_exit.assert_called_once_with(0)
