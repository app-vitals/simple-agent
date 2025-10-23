"""Tests for the main module."""

from pytest_mock import MockerFixture

from simple_agent.__main__ import main


def test_main_version(mocker: MockerFixture) -> None:
    """Test the main function with --version flag."""
    # Mock the arguments
    mocker.patch("sys.argv", ["simple-agent", "--version"])
    # Mock print_formatted_text to capture output - we need to use the fully qualified module path
    mock_print = mocker.patch("simple_agent.__main__.print_formatted_text")

    main()
    # Verify print_formatted_text was called (just checking it was called, not the exact args)
    assert mock_print.called


def test_main_run_agent(mocker: MockerFixture) -> None:
    """Test the main function normal operation."""
    # Mock the arguments
    mocker.patch("sys.argv", ["simple-agent"])

    # Mock Agent class
    mock_agent = mocker.MagicMock()
    mock_agent.mcp_manager = None  # No MCP manager in test
    mock_agent_class = mocker.patch(
        "simple_agent.__main__.Agent", return_value=mock_agent
    )

    # Mock sys.exit to avoid actually exiting
    mock_exit = mocker.patch("sys.exit")

    # Run main
    main()

    # Verify Agent was instantiated and run was called
    mock_agent_class.assert_called_once()
    mock_agent.run.assert_called_once()
    # Verify sys.exit was called with 0
    mock_exit.assert_called_once_with(0)


def test_main_keyboard_interrupt(mocker: MockerFixture) -> None:
    """Test the main function with keyboard interrupt."""
    # Mock the arguments
    mocker.patch("sys.argv", ["simple-agent"])

    # Mock Agent to raise KeyboardInterrupt
    mock_agent = mocker.MagicMock()
    mock_agent.run.side_effect = KeyboardInterrupt()
    mocker.patch("simple_agent.__main__.Agent", return_value=mock_agent)

    # Mock print_formatted_text and sys.exit - use the fully qualified path
    mock_print = mocker.patch("simple_agent.__main__.print_formatted_text")
    mock_exit = mocker.patch("sys.exit")

    # Run main
    main()

    # Verify that print_formatted_text was called and exit code
    assert mock_print.called
    mock_exit.assert_called_once_with(0)
