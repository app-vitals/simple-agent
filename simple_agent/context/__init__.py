"""Context management system for execution efficiency."""

from simple_agent.context.globals import get_context_manager, reset_context_manager
from simple_agent.context.manager import ContextManager
from simple_agent.context.schema import ContextEntry, ContextType

__all__ = [
    "ContextManager",
    "ContextEntry",
    "ContextType",
    "get_context_manager",
    "reset_context_manager",
]
