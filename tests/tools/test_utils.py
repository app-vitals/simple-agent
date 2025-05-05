"""Tests for utility functions used by tools."""

from pathlib import Path

import pytest
from pytest_mock import MockerFixture

from simple_agent.tools.utils import clean_path, format_tool_args, print_tool_call


@pytest.fixture
def mock_cwd(monkeypatch: pytest.MonkeyPatch) -> Path:
    """Mock the current working directory for consistent tests."""
    test_cwd = Path("/home/user/project")
    monkeypatch.setattr(Path, "cwd", lambda: test_cwd)
    return test_cwd


def test_clean_path(mock_cwd: Path) -> None:
    """Test the clean_path function."""
    # Test with path under CWD
    cwd_path = str(mock_cwd / "file.txt")
    assert clean_path(cwd_path) == "file.txt"

    # Test with path in subdirectory under CWD
    subdir_path = str(mock_cwd / "subdir" / "file.txt")
    assert clean_path(subdir_path) == "subdir/file.txt"

    # Test with CWD itself
    assert clean_path(str(mock_cwd)) == "."

    # Test with path outside CWD
    outside_path = "/tmp/file.txt"
    assert clean_path(outside_path) == outside_path

    # Test with relative path (should remain unchanged)
    relative_path = "relative/path.txt"
    assert clean_path(relative_path) == relative_path


def test_format_tool_args_strings(mock_cwd: Path) -> None:
    """Test formatting string arguments."""
    # Test with string argument
    path = str(mock_cwd / "file.txt")
    assert format_tool_args(path) == "'file.txt'"

    # Test with multiple string arguments
    path2 = str(mock_cwd / "another.txt")
    assert format_tool_args(path, path2) == "'file.txt', 'another.txt'"

    # Test with non-string argument
    assert format_tool_args(123) == "123"

    # Test with mixed arguments
    assert format_tool_args(path, 123, True) == "'file.txt', 123, True"


def test_format_tool_args_lists(mock_cwd: Path) -> None:
    """Test formatting list arguments."""
    # Test with list of strings
    path_list = [str(mock_cwd / "file1.txt"), str(mock_cwd / "file2.txt")]
    result = format_tool_args(path_list)
    assert "'file1.txt'" in result
    assert "'file2.txt'" in result

    # Test with empty list - the function currently returns an empty string for empty list
    assert format_tool_args([]) == ""

    # Test with list of non-strings
    assert format_tool_args([1, 2, 3]) == "[1, 2, 3]"


def test_format_tool_args_kwargs(mock_cwd: Path) -> None:
    """Test formatting keyword arguments."""
    # Test with string keyword argument
    path = str(mock_cwd / "file.txt")
    assert format_tool_args(file=path) == "file='file.txt'"

    # Test with multiple keyword arguments
    result = format_tool_args(file=path, num=42, flag=True)
    assert "file='file.txt'" in result
    assert "num=42" in result
    assert "flag=True" in result

    # Test with file_paths special case
    path_list = [str(mock_cwd / "file1.txt"), str(mock_cwd / "file2.txt")]
    result = format_tool_args(file_paths=path_list)
    assert "file1.txt, file2.txt" in result and "file_paths=" not in result

    # Test with other list keyword argument
    result = format_tool_args(paths=path_list)
    assert "paths=[" in result
    assert "'file1.txt'" in result
    assert "'file2.txt'" in result


def test_format_tool_args_combined(mock_cwd: Path) -> None:
    """Test formatting combined positional and keyword arguments."""
    path = str(mock_cwd / "file.txt")
    path_list = [str(mock_cwd / "file1.txt"), str(mock_cwd / "file2.txt")]

    result = format_tool_args(path, pattern="*.py", file_paths=path_list)
    assert "'file.txt'" in result
    assert "pattern='*.py'" in result
    assert "file1.txt, file2.txt" in result


def test_print_tool_call(mock_cwd: Path, mocker: MockerFixture) -> None:
    """Test the print_tool_call function."""
    # Mock Console.print
    mock_console_print = mocker.patch("rich.console.Console.print")

    # Test with simple tool call
    print_tool_call("test_tool", "arg1", "arg2")
    mock_console_print.assert_called_once()
    call_args = mock_console_print.call_args[0][0]
    assert "test_tool" in call_args
    assert "'arg1'" in call_args
    assert "'arg2'" in call_args

    # Reset mock
    mock_console_print.reset_mock()

    # Test with keyword arguments
    print_tool_call("read_files", file_paths=[str(mock_cwd / "file.txt")])
    mock_console_print.assert_called_once()
    call_args = mock_console_print.call_args[0][0]
    assert "read_files" in call_args
    assert "file.txt" in call_args
