"""Tests for the patch_file tool."""

import os
import tempfile
from pathlib import Path

from simple_agent.tools.files import patch_file


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
