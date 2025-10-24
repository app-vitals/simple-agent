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
    assert "/compress" in completer.commands
    assert "/mcp" in completer.commands
    assert "\\ + Enter" in completer.commands

    # Test getting completions
    doc = MagicMock()
    doc.get_word_before_cursor.return_value = "/"
    doc.text_before_cursor = "/"

    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) == 5  # /help, /exit, /clear, /compress, /mcp

    # Test that slash commands only appear at the beginning of a line
    doc.text_before_cursor = "some text /"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) == 0  # No slash commands in the middle of text


def test_file_path_completer(mocker: MockerFixture) -> None:
    """Test the FilePathCompleter class."""
    completer = FilePathCompleter()

    # Create a reusable mock response
    mock_completion = MagicMock()

    # Keep track of what the completer passes to the path_completer
    sub_documents = []

    # Create a custom mock that captures the document passed
    def mock_get_completions(document: MagicMock, _: MagicMock) -> list[MagicMock]:
        # Save the document that was passed to the path_completer
        sub_documents.append(document.text_before_cursor)
        return [mock_completion]

    # Apply the mock
    mocker.patch.object(
        completer.path_completer, "get_completions", side_effect=mock_get_completions
    )

    # Test with path starting with ./
    doc = MagicMock()
    doc.text_before_cursor = "./test"

    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield completions for ./test
    # The document passed to path_completer should be the full string
    assert sub_documents[-1] == "./test"

    # Test with path starting with ~/
    doc.text_before_cursor = "~/test"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield completions for ~/test
    # The document passed to path_completer should be the full string
    assert sub_documents[-1] == "~/test"

    # Test with path starting with /
    doc.text_before_cursor = "/usr/bin"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield completions for /usr/bin
    # The document passed to path_completer should be the full string
    assert sub_documents[-1] == "/usr/bin"

    # Test with path containing ./ in the middle
    doc.text_before_cursor = "copy ./test"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0  # Should yield completions for ./test
    # The document passed to path_completer should be just "./test"
    assert sub_documents[-1] == "./test"

    # Test with command and path pattern
    doc.text_before_cursor = "ls /usr/lo"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0
    # The document passed to path_completer should be just "/usr/lo"
    assert sub_documents[-1] == "/usr/lo"

    # Test with multiple spaces
    doc.text_before_cursor = "command with   /etc/ho"
    completions = list(completer.get_completions(doc, MagicMock()))
    assert len(completions) > 0
    # The document passed to path_completer should be just "/etc/ho"
    assert sub_documents[-1] == "/etc/ho"

    # Test with non-path input
    doc.text_before_cursor = "hello world"

    # Replace the mock with one that returns no completions
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
