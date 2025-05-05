"""Tests for the list_directory tool."""

import os
import tempfile

from pytest_mock import MockerFixture

from simple_agent.tools.files import list_directory


def test_list_directory(mocker: MockerFixture) -> None:
    """Test listing a directory."""
    # Create temporary directory structure
    temp_dir = tempfile.mkdtemp()

    # Subdirectories
    subdir1 = os.path.join(temp_dir, "subdir1")
    os.makedirs(subdir1)

    subdir2 = os.path.join(temp_dir, "subdir2")
    os.makedirs(subdir2)

    hidden_dir = os.path.join(temp_dir, ".hidden_dir")
    os.makedirs(hidden_dir)

    # Files in root
    file1_path = os.path.join(temp_dir, "file1.txt")
    with open(file1_path, "w") as f:
        f.write("File 1 content")

    file2_path = os.path.join(temp_dir, "file2.txt")
    with open(file2_path, "w") as f:
        f.write("File 2 content")

    hidden_file_path = os.path.join(temp_dir, ".hidden_file")
    with open(hidden_file_path, "w") as f:
        f.write("Hidden file content")

    # File in subdirectory
    subdir_file_path = os.path.join(subdir1, "subdir_file.txt")
    with open(subdir_file_path, "w") as f:
        f.write("Subdir file content")

    # Mock display functions to avoid output in tests
    mocker.patch("simple_agent.tools.files.list_directory.print_tool_call")
    mocker.patch("simple_agent.tools.files.list_directory.print_tool_result")
    mocker.patch("simple_agent.tools.files.list_directory.display_warning")

    try:
        # Test basic directory listing (non-recursive, no hidden files)
        result = list_directory(temp_dir)

        # Check structure and basic fields
        assert "path" in result
        assert "name" in result
        assert "dirs" in result
        assert "files" in result

        # Should have two directories and two files (hidden ones excluded by default)
        dirs_list = result["dirs"]
        files_list = result["files"]
        assert isinstance(dirs_list, list)
        assert isinstance(files_list, list)
        assert len(dirs_list) == 2  # subdir1 and subdir2
        assert len(files_list) == 2  # file1.txt and file2.txt

        # Test with show_hidden=True
        result = list_directory(temp_dir, show_hidden=True)
        dirs_list = result["dirs"]
        files_list = result["files"]
        assert isinstance(dirs_list, list)
        assert isinstance(files_list, list)
        assert len(dirs_list) == 3  # subdir1, subdir2, and .hidden_dir
        assert len(files_list) == 3  # file1.txt, file2.txt, and .hidden_file

        # Test recursive listing
        result = list_directory(temp_dir, recursive=True)

        # Find subdir1 and check it has the correct file in children
        dirs_list = result["dirs"]
        assert isinstance(dirs_list, list)

        for dir_info in dirs_list:
            if dir_info["name"] == "subdir1":
                assert "children" in dir_info
                children = dir_info["children"]
                assert isinstance(children, dict)
                child_files = children["files"]
                assert isinstance(child_files, list)
                assert len(child_files) == 1
                assert child_files[0]["name"] == "subdir_file.txt"

        # Test with non-existent directory
        non_existent = os.path.join(temp_dir, "non_existent")
        result = list_directory(non_existent)
        assert "error" in result

        # Test with a file path instead of a directory
        result = list_directory(file1_path)
        assert "error" in result

    finally:
        # Clean up temporary files and directories
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.unlink(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)
