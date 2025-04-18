"""Tests for the files module."""

import os
import tempfile
from pathlib import Path

from simple_agent.tools.files import patch_file, read_files, write_file


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
