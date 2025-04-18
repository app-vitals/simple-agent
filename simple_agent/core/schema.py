"""Schema definitions for the agent."""

from enum import Enum

from pydantic import BaseModel, Field


class AgentStatus(str, Enum):
    """Agent response status."""

    COMPLETE = "COMPLETE"  # Task is finished
    CONTINUE = "CONTINUE"  # Agent can continue automatically
    ASK = "ASK"  # Agent needs user input


class AgentResponse(BaseModel):
    """Structured response format for the agent."""

    message: str = Field(description="Main message and analysis for the user")
    status: AgentStatus = Field(description="Current status of the task")
    next_action: str | None = Field(
        None,
        description="Description of what happens next (continue action or question for user)",
    )
