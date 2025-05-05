"""Utility functions for tools."""

from pathlib import Path


def clean_path(path: str) -> str:
    """Remove current working directory prefix from a path for display.

    Args:
        path: Path string to clean

    Returns:
        Path without CWD prefix, or unchanged if not under CWD
    """
    cwd = str(Path.cwd())
    if path.startswith(cwd):
        # Strip current working directory and any leading slashes
        clean = path[len(cwd) :].lstrip("/") or "."
        return clean
    return path


def format_tool_args(*args: object, **kwargs: object) -> str:
    """Format tool arguments for display by removing CWD prefixes.

    Args:
        *args: Positional arguments to format
        **kwargs: Keyword arguments to format

    Returns:
        String representation of arguments with clean paths
    """
    # Format positional arguments
    formatted_args = []
    for arg in args:
        if isinstance(arg, str):
            formatted_args.append(f"'{clean_path(arg)}'")
        elif isinstance(arg, list | tuple) and all(isinstance(x, str) for x in arg):
            # For lists/tuples of strings, clean each path and format as comma-separated
            formatted_items = [f"'{clean_path(x)}'" for x in arg]
            formatted_args.append(", ".join(formatted_items))
        else:
            formatted_args.append(str(arg))

    # Format keyword arguments
    formatted_kwargs = []
    for key, value in kwargs.items():
        if isinstance(value, str):
            formatted_kwargs.append(f"{key}='{clean_path(value)}'")
        elif isinstance(value, list | tuple) and all(isinstance(x, str) for x in value):
            # Special handling for file_paths which should be displayed as comma-separated values
            if key == "file_paths":
                cleaned_paths = [clean_path(x) for x in value]
                formatted_kwargs.append(", ".join(cleaned_paths))
            else:
                # For other lists/tuples, format as a list
                formatted_items = [f"'{clean_path(x)}'" for x in value]
                formatted_kwargs.append(f"{key}=[{', '.join(formatted_items)}]")
        else:
            formatted_kwargs.append(f"{key}={value}")

    # Combine positional and keyword arguments
    all_args = []
    if formatted_args:
        all_args.extend(formatted_args)
    if formatted_kwargs:
        all_args.extend(formatted_kwargs)

    return ", ".join(all_args)


def print_tool_call(tool_name: str, *args: object, **kwargs: object) -> None:
    """Print a tool call with cleaned path arguments.

    Args:
        tool_name: Name of the tool being called
        *args: Positional arguments to the tool
        **kwargs: Keyword arguments to the tool
    """
    from rich.console import Console

    console = Console()
    formatted_args = format_tool_args(*args, **kwargs)
    console.print(f"{tool_name}({formatted_args})")
