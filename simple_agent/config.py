"""Configuration module for Simple Agent."""

import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables from .env file
load_dotenv()


class LLMConfig(BaseModel):
    """LLM configuration settings."""

    api_key: str | None = Field(
        default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY"),
        description="API key for the LLM service",
    )
    model: str = Field(
        default_factory=lambda: os.environ.get("LLM_MODEL", "claude-3-haiku-20240307"),
        description="LLM model to use",
    )


class Config(BaseModel):
    """Application configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)


# Global config instance
config = Config()
