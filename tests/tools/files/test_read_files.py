"""Tests for the read_files tool."""

import os
import tempfile

from simple_agent.tools.files import read_files


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
