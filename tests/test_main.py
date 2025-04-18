"""Tests for the main module."""

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
