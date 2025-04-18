"""Tests for the files module."""

import os
import tempfile
from pathlib import Path

from simple_agent.tools import files


def test_read_file() -> None:
    """Test reading a file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.write(b"Hello, world!")
        temp_path = temp_file.name

    try:
        # Test reading existing file
        content = files.read_file(temp_path)
        assert content == "Hello, world!"

        # Test reading non-existent file
        non_existent_path = "/path/that/does/not/exist.txt"
        content = files.read_file(non_existent_path)
        assert content is None
    finally:
        os.unlink(temp_path)


def test_write_file() -> None:
    """Test writing to a file."""
    temp_dir = tempfile.mkdtemp()
    temp_path = os.path.join(temp_dir, "test_file.txt")

    try:
        # Test writing to a file
        result = files.write_file(temp_path, "Test content")
        assert result is True
        assert Path(temp_path).read_text() == "Test content"

        # Test writing to a non-writable location
        non_writable_path = "/root/test_file.txt"
        result = files.write_file(non_writable_path, "Test content")
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
        result = files.patch_file(temp_path, "Hello", "Hi")
        assert result is True
        assert Path(temp_path).read_text() == "Hi, world!"

        # Test patch with non-existent content
        result = files.patch_file(temp_path, "Goodbye", "Bye")
        assert result is False

        # Test patch with non-existent file
        non_existent_path = "/path/that/does/not/exist.txt"
        result = files.patch_file(non_existent_path, "Hello", "Hi")
        assert result is False
    finally:
        os.unlink(temp_path)
