"""Tests for the completion module."""

from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from simple_agent.cli.completion import CommandCompleter, Completer, FilePathCompleter


def test_command_completer() -> None:
    """Test the CommandCompleter class."""
    completer = CommandCompleter()

    # Verify commands contain the expected special commands
    assert "/help" in completer.commands
    assert "/exit" in completer.commands
    assert "/clear" in completer.commands
    assert "\\ + Enter" in completer.commands

    # Test getting completions
    doc = MagicMock()
    doc.get_word_before_cursor.return_value = "/"
    doc.text_before_cursor = "/"

    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) == 3  # /help, /exit, /clear

    # Test that slash commands only appear at the beginning of a line
    doc.text_before_cursor = "some text /"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) == 0  # No slash commands in the middle of text


def test_file_path_completer(mocker: MockerFixture) -> None:
    """Test the FilePathCompleter class."""
    completer = FilePathCompleter()

    # Create a reusable mock response
    mock_completion = MagicMock()

    # Test with path starting with ./
    doc = MagicMock()
    doc.text_before_cursor = "./test"

    mocker.patch.object(
        completer.path_completer, "get_completions", return_value=[mock_completion]
    )
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield completions for ./test

    # Test with path starting with ~/
    doc.text_before_cursor = "~/test"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield completions for ~/test

    # Test with path starting with /
    doc.text_before_cursor = "/usr/bin"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield completions for /usr/bin

    # Test with path containing ./ in the middle
    doc.text_before_cursor = "copy ./test"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield completions for ./test

    # Test with non-path input
    doc.text_before_cursor = "hello world"

    # Remove the mock so it returns the actual empty result for non-path inputs
    mocker.patch.object(completer.path_completer, "get_completions", return_value=[])
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) == 0  # Should not yield completions for non-path


def test_completer(mocker: MockerFixture) -> None:
    """Test the main Completer class that combines command and file completions."""
    completer = Completer()

    # Test with command completion (should return command completions)
    doc = MagicMock()
    doc.get_word_before_cursor.return_value = "/"
    doc.text_before_cursor = "/"

    # Use mocker to patch the command_completer
    mocker.patch.object(
        completer.command_completer, "get_completions", return_value=[MagicMock()]
    )

    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield command completions

    # Test with file path (should fall back to file completions)
    doc.get_word_before_cursor.return_value = ""
    doc.text_before_cursor = "./test"

    # Reset the mocks
    mocker.patch.object(completer.command_completer, "get_completions", return_value=[])
    mocker.patch.object(
        completer.file_completer, "get_completions", return_value=[MagicMock()]
    )

    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield file completions
