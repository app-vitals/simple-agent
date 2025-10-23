"""Tests for file tool format_result functions."""

from simple_agent.tools.files.read_files import format_read_files_result


def test_format_read_files_single_success() -> None:
    """Test formatting read_files result with single successful read."""
    content = "{'file.txt': 'content here'}"
    result = format_read_files_result(content)
    assert "1 file" in result or "File read" in result
    assert "[green]" in result


def test_format_read_files_multiple_success() -> None:
    """Test formatting read_files result with multiple successful reads."""
    content = (
        "{'file1.txt': 'content1', 'file2.txt': 'content2', 'file3.txt': 'content3'}"
    )
    result = format_read_files_result(content)
    assert "3 files" in result
    assert "[green]" in result


def test_format_read_files_partial_failure() -> None:
    """Test formatting read_files result with some failures."""
    content = "{'file1.txt': 'content', 'file2.txt': None, 'file3.txt': 'content'}"
    result = format_read_files_result(content)
    assert "2/3" in result
    assert "1 failed" in result
    assert "[yellow]" in result


def test_format_read_files_invalid_format() -> None:
    """Test formatting read_files with invalid format."""
    content = "invalid content"
    result = format_read_files_result(content)
    # Should fallback to simple message
    assert "✓" in result
    assert "[dim]" in result
