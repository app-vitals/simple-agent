"""Tests for the grep_files tool."""

import os
import tempfile
from typing import Any

from pytest_mock import MockerFixture

from simple_agent.tools.files import grep_files
from simple_agent.tools.files.grep_files import (
    _matches_pattern,
    _simple_pattern_match,
)


def test_grep_files(mocker: MockerFixture) -> None:
    """Test searching file contents for patterns."""
    # Create temporary directory structure
    temp_dir = tempfile.mkdtemp()

    # Create test files with content
    python_file = os.path.join(temp_dir, "test.py")
    with open(python_file, "w") as f:
        f.write(
            "def hello_world():\n    print('Hello, world!')\n\n# A comment line\ndef goodbye():\n    print('Goodbye!')"
        )

    js_file = os.path.join(temp_dir, "test.js")
    with open(js_file, "w") as f:
        f.write(
            "function hello() {\n    console.log('Hello!');\n}\n\n// Another comment\nfunction goodbye() {\n    console.log('Goodbye!');\n}"
        )

    txt_file = os.path.join(temp_dir, "test.txt")
    with open(txt_file, "w") as f:
        f.write(
            "This is a text file\nIt contains the word hello\nAnd also HELLO in uppercase\nAnd Goodbye too!"
        )

    hidden_file = os.path.join(temp_dir, ".hidden.txt")
    with open(hidden_file, "w") as f:
        f.write("This is a hidden file\nIt also contains hello and goodbye")

    # Create subdirectory with a file
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    subdir_file = os.path.join(subdir, "sub.txt")
    with open(subdir_file, "w") as f:
        f.write("This is in a subdirectory\nIt contains hello and goodbye")

    # Create test file with imports for MockerFixture
    test_file = os.path.join(temp_dir, "test_mock.py")
    with open(test_file, "w") as f:
        f.write(
            "from pytest_mock import MockerFixture\n\ndef test_something(mocker: MockerFixture):\n    mock = mocker.patch('some.module')\n    assert True"
        )

    # Create an unreadable file
    binary_file = os.path.join(temp_dir, "binary.bin")
    with open(binary_file, "wb") as binary_f:
        binary_f.write(b"\x00\x01\x02\x03\x04")

    # Mock display functions to avoid output in tests
    mocker.patch("simple_agent.tools.files.grep_files.print_tool_call")
    mocker.patch("simple_agent.tools.files.grep_files.print_tool_result")
    mocker.patch("simple_agent.tools.files.grep_files.display_warning")

    try:
        # Test basic pattern search across multiple files
        result = grep_files(pattern="hello", directory=temp_dir)
        assert len(result) >= 2  # Should find matches in multiple files

        # Files may have different paths due to symlinks or temp dirs
        # So check for the filenames instead of the full paths
        file_basenames = [os.path.basename(path) for path in result]
        assert "test.txt" in file_basenames
        assert any(basename in ["test.py", "test.js"] for basename in file_basenames)

        # Check specific line matches
        found_hello_content = False
        for _file_path, matches in result.items():
            for _, line_content in matches:
                if "hello" in line_content.lower():
                    found_hello_content = True
                    break
        assert found_hello_content

        # Test case-sensitive search
        result = grep_files(pattern="hello", directory=temp_dir, case_sensitive=True)
        # Count how many matches contain "HELLO" in uppercase
        uppercase_matches = 0
        for _file_path, matches in result.items():
            for _, line_content in matches:
                if "HELLO" in line_content:
                    uppercase_matches += 1

        # There should be no uppercase matches with case_sensitive=True
        assert uppercase_matches == 0

        # Test include_pattern
        result = grep_files(
            pattern="function", directory=temp_dir, include_pattern="*.js"
        )
        assert len(result) == 1  # Should only find in JS file
        assert any("test.js" in os.path.basename(path) for path in result)

        # Test recursive search
        result = grep_files(pattern="hello", directory=temp_dir, recursive=True)
        file_basenames = [os.path.basename(path) for path in result]
        assert "sub.txt" in file_basenames  # Should find in subdirectory

        # Test with non-existent directory
        result = grep_files(
            pattern="hello", directory=os.path.join(temp_dir, "nonexistent")
        )
        assert "error" in result  # Should return an error

        # Test hidden files
        result = grep_files(pattern="hidden", directory=temp_dir, include_hidden=True)
        assert len(result) == 1  # Should find in .hidden.txt
        assert any(".hidden.txt" in os.path.basename(path) for path in result)

        # Test without including hidden files
        result = grep_files(pattern="hidden", directory=temp_dir, include_hidden=False)
        assert not any(".hidden.txt" in os.path.basename(path) for path in result)

        # Test specific file paths
        result = grep_files(pattern="goodbye", file_paths=[python_file, txt_file])
        assert len(result) >= 1  # Should find in at least one of the specified files
        file_basenames = [os.path.basename(path) for path in result]
        assert any(basename in ["test.py", "test.txt"] for basename in file_basenames)

        # Test with non-existent file path
        non_existent_file = os.path.join(temp_dir, "nonexistent.txt")
        result = grep_files(pattern="hello", file_paths=[non_existent_file])
        assert len(result) == 0  # Should be empty as the file doesn't exist

        # Test regex pattern
        result = grep_files(pattern=r"print\(.*\)", directory=temp_dir)
        file_basenames = [os.path.basename(path) for path in result]
        assert "test.py" in file_basenames  # Should find in python file

        # Test file pattern with braces
        result = grep_files(
            pattern="function", directory=temp_dir, include_pattern="*.{js,py}"
        )
        assert any(
            "test.js" in os.path.basename(path) for path in result
        )  # Should find in js file

        # Test context lines
        result = grep_files(pattern="hello", directory=temp_dir, context_lines=1)
        for _file_path, matches in result.items():
            # When we find hello, check that there are more lines than just the match
            if any("hello" in line.lower() for _, line in matches):
                assert len(matches) > 1  # Should have more than just the matching line

        # Test MockerFixture search specifically
        result = grep_files(pattern="MockerFixture", directory=temp_dir)
        assert any("test_mock.py" in os.path.basename(path) for path in result), (
            f"Failed to find MockerFixture in test_mock.py. "
            f"Got paths: {list(result.keys())}"
        )

        # Test matching pattern functions directly
        # Simple pattern match
        assert _simple_pattern_match("file.txt", "*.txt") is True
        assert _simple_pattern_match("file.js", "*.txt") is False
        assert _simple_pattern_match("prefix_file", "prefix_*") is True

        # Complex pattern match with braces
        assert _matches_pattern("file.js", "*.{js,py}") is True
        assert _matches_pattern("file.py", "*.{js,py}") is True
        assert _matches_pattern("file.txt", "*.{js,py}") is False

        # Test with max_results
        result = grep_files(pattern="e", directory=temp_dir, max_results=5)
        total_matches = sum(len(matches) for matches in result.values())
        assert total_matches <= 5  # Should limit results to 5

        # Test error handling with binary file (using file_paths to simplify)
        # First, create a copy of the txt_file for use in our test
        txt_file_copy = os.path.join(temp_dir, "test_copy.txt")
        with open(txt_file_copy, "w") as f:
            f.write("This is a copy with hello in it")

        # Mock open to raise an exception for binary file but work for txt_file_copy
        original_open = open

        def mock_open_with_exception(*args: Any, **kwargs: Any) -> Any:
            file_path = args[0] if args else kwargs.get("file")
            if file_path == binary_file and kwargs.get("mode", "r") != "wb":
                raise UnicodeDecodeError(
                    "utf-8", b"\x00\x01\x02\x03", 0, 1, "invalid start byte"
                )
            return original_open(*args, **kwargs)

        # Use the mock only for the binary file test
        open_patcher = mocker.patch(
            "builtins.open", side_effect=mock_open_with_exception
        )
        result = grep_files(pattern="hello", file_paths=[binary_file, txt_file_copy])
        assert any("test_copy.txt" in os.path.basename(path) for path in result)
        assert not any("binary.bin" in os.path.basename(path) for path in result)
        open_patcher.stop()

        # Test invalid regex pattern
        result = grep_files(pattern="[invalid", directory=temp_dir)
        assert "error" in result  # Should return an error

    finally:
        # Clean up temporary files and directories
        for root, dirs, files in os.walk(temp_dir, topdown=False):
            for file in files:
                os.unlink(os.path.join(root, file))
            for dir in dirs:
                os.rmdir(os.path.join(root, dir))
        os.rmdir(temp_dir)
