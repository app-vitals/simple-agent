"""Load markdown context files from context/ directory."""

from pathlib import Path


def load_context_from_directory(context_dir: Path | str | None = None) -> str:
    """Load all markdown files from the context directory.

    Args:
        context_dir: Path to context directory. Defaults to <cwd>/context/

    Returns:
        Combined context from all markdown files
    """
    context_dir = Path.cwd() / "context" if context_dir is None else Path(context_dir)

    if not context_dir.exists() or not context_dir.is_dir():
        return ""

    # Find all markdown files
    markdown_files = sorted(context_dir.glob("*.md"))

    if not markdown_files:
        return ""

    # Load and combine all markdown files
    context_parts = []
    for md_file in markdown_files:
        try:
            with open(md_file, encoding="utf-8") as f:
                content = f.read().strip()
                if content:
                    # Add file header for context
                    context_parts.append(f"# Context from {md_file.name}\n\n{content}")
        except Exception as e:
            # Skip files that can't be read
            print(f"Warning: Could not read context file {md_file}: {e}")
            continue

    return "\n\n---\n\n".join(context_parts)
