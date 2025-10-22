"""Schema definitions for context entries."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ContextType(str, Enum):
    """Types of context entries."""

    MANUAL = "manual"  # User-provided context
    FILE = "file"  # File read/write operations
    CALENDAR = "calendar"  # Calendar events
    TASK = "task"  # Jira/Linear tasks
    TIME_TRACKING = "time_tracking"  # Time tracking entries (Toggl, etc)
    GOAL = "goal"  # Long-term goals


class ContextEntry(BaseModel):
    """A single context entry."""

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    id: str = Field(default_factory=lambda: str(uuid4()))
    type: ContextType
    source: str  # e.g., "user", "google_calendar", "jira"
    content: str  # Human-readable context description
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ContextStore(BaseModel):
    """Container for all context entries."""

    model_config = ConfigDict(ser_json_timedelta="iso8601")

    version: str = "1.0"
    entries: list[ContextEntry] = Field(default_factory=list)
