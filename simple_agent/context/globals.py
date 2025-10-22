"""Global context manager instance.

This module provides a singleton context manager that can be accessed
throughout the application.
"""

from simple_agent.context.manager import ContextManager

# Global context manager instance
_context_manager: ContextManager | None = None


def get_context_manager() -> ContextManager:
    """Get or create the global context manager instance.

    Returns:
        The global ContextManager instance
    """
    global _context_manager
    if _context_manager is None:
        _context_manager = ContextManager()
    return _context_manager


def reset_context_manager() -> None:
    """Reset the global context manager (primarily for testing)."""
    global _context_manager
    _context_manager = None
