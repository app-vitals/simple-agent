"""Tests for the glob_files tool."""

import os
import tempfile

from pytest_mock import MockerFixture

from simple_agent.tools.files import glob_files


def test_glob_files(mocker: MockerFixture) -> None:
    """Test finding files using glob patterns."""
    # Create temporary directory structure
    temp_dir = tempfile.mkdtemp()

    # Create subdirectory
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)

    # Create files with different extensions
    py_file1 = os.path.join(temp_dir, "file1.py")
    py_file2 = os.path.join(temp_dir, "file2.py")
    txt_file = os.path.join(temp_dir, "file.txt")
    subdir_py_file = os.path.join(subdir, "subfile.py")
    hidden_file = os.path.join(temp_dir, ".hidden.py")

    # Create the files
    for file_path in [py_file1, py_file2, txt_file, subdir_py_file, hidden_file]:
        with open(file_path, "w") as f:
            f.write(f"Content of {os.path.basename(file_path)}")

    # Mock display functions to avoid output in tests
    mocker.patch("simple_agent.tools.files.glob_files.print_tool_call")
    mocker.patch("simple_agent.tools.files.glob_files.print_tool_result")
    mocker.patch("simple_agent.tools.files.glob_files.display_error")
    mocker.patch("simple_agent.tools.files.glob_files.display_info")

    try:
        # Test basic glob matching
        result = glob_files("*.py", base_dir=temp_dir)
        assert len(result) == 2  # Should find file1.py and file2.py
        assert os.path.basename(result[0]) in ["file1.py", "file2.py"]
        assert os.path.basename(result[1]) in ["file1.py", "file2.py"]

        # Test with different pattern
        result = glob_files("*.txt", base_dir=temp_dir)
        assert len(result) == 1
        assert os.path.basename(result[0]) == "file.txt"

        # Test recursive glob with **
        result = glob_files("**/*.py", base_dir=temp_dir)
        assert len(result) == 3  # Should find all .py files including in subdirectory

        # Test include_hidden
        result = glob_files("*.py", base_dir=temp_dir, include_hidden=True)
        assert len(result) == 3  # Should find file1.py, file2.py, and .hidden.py

        # Test with non-existent directory
        non_existent = os.path.join(temp_dir, "non_existent")
        result = glob_files("*.py", base_dir=non_existent)
        assert result == []  # Should return empty list

        # Test with file path instead of directory
        result = glob_files("*.py", base_dir=py_file1)
        assert result == []  # Should return empty list

    finally:
        # Clean up temporary files and directories
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.unlink(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)
