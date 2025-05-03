"""Tests for the write_file tool."""

import os
import tempfile
from pathlib import Path

from simple_agent.tools.files import write_file


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
