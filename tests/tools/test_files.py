"""Tests for the files module."""

import os
import tempfile
from pathlib import Path

from pytest_mock import MockerFixture

from simple_agent.tools.files import (
    glob_files,
    list_directory,
    patch_file,
    read_files,
    write_file,
)


def test_read_files() -> None:
    """Test reading files."""
    # Create a couple of temporary files
    with tempfile.NamedTemporaryFile(delete=False) as temp_file1:
        temp_file1.write(b"Hello, world!")
        temp_path1 = temp_file1.name

    with tempfile.NamedTemporaryFile(delete=False) as temp_file2:
        temp_file2.write(b"Testing, 123!")
        temp_path2 = temp_file2.name

    try:
        # Test reading a single file
        content = read_files([temp_path1])
        assert temp_path1 in content
        assert content[temp_path1] == "Hello, world!"

        # Test reading multiple files
        content = read_files([temp_path1, temp_path2])
        assert len(content) == 2
        assert content[temp_path1] == "Hello, world!"
        assert content[temp_path2] == "Testing, 123!"

        # Test reading a mix of existing and non-existent files
        non_existent_path = "/path/that/does/not/exist.txt"
        content = read_files([temp_path1, non_existent_path])
        assert content[temp_path1] == "Hello, world!"
        assert content[non_existent_path] is None
    finally:
        os.unlink(temp_path1)
        os.unlink(temp_path2)


def test_write_file() -> None:
    """Test writing to a file."""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "test_file.txt")

    try:
        # Test writing to a file
        result = write_file(temp_path, "Test content")
        assert result is True
        assert Path(temp_path).read_text() == "Test content"

        # Test writing to a non-writable location
        non_writable_path = "/root/test_file.txt"
        result = write_file(non_writable_path, "Test content")
        assert result is False
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        os.rmdir(temp_dir)


def test_patch_file() -> None:
    """Test patching a file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Hello, world!")
        temp_path = temp_file.name

    try:
        # Test successful patch
        result = patch_file(temp_path, "Hello", "Hi")
        assert result is True
        assert Path(temp_path).read_text() == "Hi, world!"

        # Test patch with non-existent content
        result = patch_file(temp_path, "Goodbye", "Bye")
        assert result is False

        # Test patch with non-existent file
        non_existent_path = "/path/that/does/not/exist.txt"
        result = patch_file(non_existent_path, "Hello", "Hi")
        assert result is False
    finally:
        os.unlink(temp_path)


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

    # Mock console.print to avoid output in tests
    mocker.patch("simple_agent.tools.files.Console.print")

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

    # Mock console.print to avoid output in tests
    mocker.patch("simple_agent.tools.files.Console.print")

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
