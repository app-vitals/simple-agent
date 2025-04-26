"""Tests for the completion module."""

from unittest.mock import MagicMock

from simple_agent.cli.completion import CommandCompleter


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
