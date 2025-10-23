"""Configuration module for Simple Agent."""

import json
import os
from pathlib import Path

from dotenv import load_dotenv
from pydantic import BaseModel, Field

from simple_agent.display import display_warning

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


class MCPServerConfig(BaseModel):
    """Configuration for a single MCP server."""

    command: str = Field(description="Command to execute the MCP server")
    args: list[str] = Field(
        default_factory=list, description="Arguments to pass to the server command"
    )
    env: dict[str, str] = Field(
        default_factory=dict, description="Environment variables for the server"
    )


class Config(BaseModel):
    """Application configuration."""

    llm: LLMConfig = Field(default_factory=LLMConfig)
    mcp_servers: dict[str, MCPServerConfig] = Field(default_factory=dict)
    mcp_disabled: bool = Field(
        default_factory=lambda: os.environ.get(
            "SIMPLE_AGENT_DISABLE_MCP", "false"
        ).lower()
        == "true",
        description="Disable MCP server initialization",
    )


def load_mcp_config() -> dict[str, MCPServerConfig]:
    """Load MCP server configuration from ~/.simple-agent/mcp_servers.json if it exists.

    Returns:
        Dictionary of MCP server configurations
    """
    config_dir = Path.home() / ".simple-agent"
    config_path = config_dir / "mcp_servers.json"

    if not config_path.exists():
        return {}

    try:
        with open(config_path) as f:
            data = json.load(f)
            return {
                name: MCPServerConfig.model_validate(server_config)
                for name, server_config in data.items()
            }
    except Exception as e:
        # Show warning if config file is invalid
        display_warning(f"Failed to load {config_path}", e)
        return {}


# Global config instance
config = Config(mcp_servers=load_mcp_config())
