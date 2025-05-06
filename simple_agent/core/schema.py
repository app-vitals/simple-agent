"""Schema definitions for the agent."""

from enum import Enum

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent response status."""

    COMPLETE = "COMPLETE"  # Task is finished
    ASK = "ASK"  # Agent needs user input


class AgentResponse(BaseModel):
    """Structured response format for the agent."""

    message: str = Field(description="Main message and analysis for the user")
    status: AgentStatus = Field(description="Current status of the task")
    question: str | None = Field(
        None,
        description="The question to ask the user",
    )
