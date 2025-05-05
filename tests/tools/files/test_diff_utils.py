"""Tests for the diff_utils module."""

from unittest.mock import MagicMock, patch

from simple_agent.tools.files.diff_utils import (
    create_git_diff_view,
    get_file_diff_for_patch,
    get_file_diff_for_write,
    patch_file_confirmation_handler,
    show_git_diff_confirmation,
    write_file_confirmation_handler,
)


def test_create_git_diff_view_new_file() -> None:
    """Test creating a git diff view for a new file."""
    file_path = "/path/to/new_file.txt"
    old_content = ""
    new_content = "Line 1\nLine 2\nLine 3"

    diff = create_git_diff_view(file_path, old_content, new_content)

    # Check the diff format for a new file
    assert "diff --git" in diff
    assert "new file mode" in diff
    assert "--- /dev/null" in diff
    assert "+++ b/" in diff
    assert "@@ -0,0 +1,3 @@" in diff
    assert "+Line 1" in diff
    assert "+Line 2" in diff
    assert "+Line 3" in diff


def test_create_git_diff_view_modified_file() -> None:
    """Test creating a git diff view for a modified file."""
    file_path = "/path/to/existing_file.txt"
    old_content = "Line 1\nLine 2\nLine 3"
    new_content = "Line 1\nModified Line\nLine 3"

    diff = create_git_diff_view(file_path, old_content, new_content)

    # Check the diff format for a modified file
    assert "--- a/" in diff
    assert "+++ b/" in diff
    assert "-Line 2" in diff
    assert "+Modified Line" in diff


@patch("simple_agent.tools.files.diff_utils.Path")
def test_get_file_diff_for_write_new_file(mock_path: MagicMock) -> None:
    """Test generating a diff for a write operation (new file)."""
    # Mock the Path.exists() call to return False (new file)
    mock_path.return_value.exists.return_value = False

    file_path = "/path/to/new_file.txt"
    content = "New content"

    diff = get_file_diff_for_write(file_path, content)

    # Should create a new file diff
    assert "new file mode" in diff
    assert "--- /dev/null" in diff
    assert "+New content" in diff


@patch("simple_agent.tools.files.diff_utils.Path")
def test_get_file_diff_for_write_existing_file(mock_path: MagicMock) -> None:
    """Test generating a diff for a write operation (existing file)."""
    # Mock the Path.exists() call to return True (existing file)
    mock_path.return_value.exists.return_value = True
    mock_path.return_value.read_text.return_value = "Original content"

    file_path = "/path/to/existing_file.txt"
    content = "New content"

    diff = get_file_diff_for_write(file_path, content)

    # Should create a modified file diff
    assert "-Original content" in diff
    assert "+New content" in diff


@patch("simple_agent.tools.files.diff_utils.Path")
def test_get_file_diff_for_patch(mock_path: MagicMock) -> None:
    """Test generating a diff for a patch operation."""
    # Mock the Path.read_text() call
    mock_path.return_value.read_text.return_value = "Line 1\nOld Line\nLine 3"

    file_path = "/path/to/file.txt"
    old_content = "Old Line"
    new_content = "New Line"

    diff = get_file_diff_for_patch(file_path, old_content, new_content)

    # Should show a diff with the old line removed and new line added
    assert "-Old Line" in diff
    assert "+New Line" in diff


@patch("simple_agent.tools.files.diff_utils.Path")
def test_get_file_diff_for_patch_content_not_found(mock_path: MagicMock) -> None:
    """Test generating a diff for a patch operation when old content is not found."""
    # Mock the Path.read_text() call
    mock_path.return_value.read_text.return_value = (
        "This content doesn't have the old text"
    )

    file_path = "/path/to/file.txt"
    old_content = "Not present"
    new_content = "New content"

    diff = get_file_diff_for_patch(file_path, old_content, new_content)

    # Should return an error message
    assert "ERROR: Old content not found" in diff


@patch("simple_agent.tools.files.diff_utils.get_confirmation")
def test_show_git_diff_confirmation_yes(mock_get_confirmation: MagicMock) -> None:
    """Test showing a git diff and getting confirmation (user says yes)."""
    # Mock get_confirmation to return True (user confirmed)
    mock_get_confirmation.return_value = True

    # Create a mock input function (this should be bypassed for the built-in input function)
    def mock_input_func(_: str) -> str:
        return "y"

    # For this test, we'll use Python's built-in input which triggers get_confirmation
    result = show_git_diff_confirmation("sample diff", "test_tool", input)

    # Should return True for confirmation
    assert result is True
    mock_get_confirmation.assert_called_once()


def test_show_git_diff_confirmation_no() -> None:
    """Test showing a git diff and getting confirmation (user says no)."""

    # Create a custom input function that returns 'n'
    def mock_input_func(_: str) -> str:
        return "n"

    # Test with a custom input function (bypasses get_confirmation)
    result = show_git_diff_confirmation("sample diff", "test_tool", mock_input_func)

    # Should return False for rejection
    assert result is False


@patch("simple_agent.tools.files.diff_utils.get_file_diff_for_write")
@patch("simple_agent.tools.files.diff_utils.show_git_diff_confirmation")
def test_write_file_confirmation_handler(
    mock_show_confirmation: MagicMock, mock_get_diff: MagicMock
) -> None:
    """Test the write_file confirmation handler."""
    # Mock the diff generation and confirmation
    mock_get_diff.return_value = "sample diff"
    mock_show_confirmation.return_value = True

    # Create a mock input function
    def mock_input_func(_: str) -> str:
        return "y"

    # Create sample tool arguments
    tool_args = {"file_path": "/path/to/file.txt", "content": "content"}

    result = write_file_confirmation_handler("write_file", tool_args, mock_input_func)

    # Should call get_file_diff_for_write with the right args
    mock_get_diff.assert_called_once_with("/path/to/file.txt", "content")

    # Should call show_git_diff_confirmation with the right args
    mock_show_confirmation.assert_called_once_with(
        "sample diff", "write_file", mock_input_func, {"file_path": "/path/to/file.txt"}
    )

    # Should return the result from show_git_diff_confirmation
    assert result is True


@patch("simple_agent.tools.files.diff_utils.get_file_diff_for_patch")
@patch("simple_agent.tools.files.diff_utils.show_git_diff_confirmation")
def test_patch_file_confirmation_handler(
    mock_show_confirmation: MagicMock, mock_get_diff: MagicMock
) -> None:
    """Test the patch_file confirmation handler."""
    # Mock the diff generation and confirmation
    mock_get_diff.return_value = "sample diff"
    mock_show_confirmation.return_value = True

    # Create a mock input function
    def mock_input_func(_: str) -> str:
        return "y"

    # Create sample tool arguments
    tool_args = {
        "file_path": "/path/to/file.txt",
        "old_content": "old content",
        "new_content": "new content",
    }

    result = patch_file_confirmation_handler("patch_file", tool_args, mock_input_func)

    # Should call get_file_diff_for_patch with the right args
    mock_get_diff.assert_called_once_with(
        "/path/to/file.txt", "old content", "new content"
    )

    # Should call show_git_diff_confirmation with the right args
    mock_show_confirmation.assert_called_once_with(
        "sample diff", "patch_file", mock_input_func, {"file_path": "/path/to/file.txt"}
    )

    # Should return the result from show_git_diff_confirmation
    assert result is True
