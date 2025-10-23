"""MCP tool adapter for converting MCP tools to registry format."""

from typing import Any

from simple_agent.display import display_error, print_tool_call
from simple_agent.tools.mcp.manager import MCPServerManager
from simple_agent.tools.registry import register


class MCPToolAdapter:
    """Adapts MCP tools to the simple-agent tool registry."""

    def __init__(self, manager: MCPServerManager) -> None:
        """Initialize the MCP tool adapter.

        Args:
            manager: The MCP server manager instance
        """
        self.manager = manager

    def discover_and_register_tools_sync(self, server_name: str) -> None:
        """Discover tools from an MCP server and register them synchronously.

        Args:
            server_name: Name of the server to discover tools from

        Raises:
            Exception: If tool discovery or registration fails
        """
        # Get tools from the MCP server
        tools = self.manager.list_tools_sync(server_name)

        # Register each tool
        for tool in tools:
            self._register_mcp_tool(server_name, tool)

    def _register_mcp_tool(self, server_name: str, tool: Any) -> None:
        """Register a single MCP tool with the tool registry.

        Args:
            server_name: Name of the MCP server hosting this tool
            tool: MCP tool definition (has name, description, inputSchema)
        """
        tool_name = tool.name
        description = tool.description
        input_schema = tool.inputSchema

        # Create wrapper function that bridges async MCP to sync tool interface
        def tool_wrapper(**kwargs: Any) -> Any:
            # Display tool call
            print_tool_call(tool_name, **kwargs)

            try:
                # Call MCP server using sync method (uses background event loop)
                result = self.manager.call_tool_sync(server_name, tool_name, kwargs)

                # MCP tools return a list of content items
                # Extract text content from the result
                if isinstance(result, list) and len(result) > 0:
                    # Get the first content item
                    content_item = result[0]
                    if hasattr(content_item, "text"):
                        return content_item.text
                    elif isinstance(content_item, dict) and "text" in content_item:
                        return content_item["text"]

                # If result doesn't match expected format, return as-is
                return result

            except Exception as e:
                error_msg = f"MCP tool '{tool_name}' failed: {str(e)}"
                display_error(error_msg, e)
                return {"error": error_msg}

        # Convert MCP inputSchema to registry parameters format
        # MCP already uses JSON Schema, which is compatible with OpenAI format
        parameters, required = self._convert_input_schema(input_schema)

        # Register with the tool registry
        # Require confirmation for MCP tools by default for safety
        register(
            name=tool_name,
            function=tool_wrapper,
            description=description,
            parameters=parameters,
            required=required,
            returns="Tool execution result",
            requires_confirmation=True,
            format_result=lambda content: "[dim]✓ Tool executed[/dim]",
        )

    def _convert_input_schema(
        self, input_schema: dict[str, Any]
    ) -> tuple[dict[str, Any], list[str]]:
        """Convert MCP inputSchema to registry parameters format.

        MCP uses JSON Schema which is already compatible with OpenAI format.
        We just need to extract the properties from the schema and ensure
        all parameters have descriptions.

        Args:
            input_schema: MCP tool input schema (JSON Schema)

        Returns:
            Tuple of (parameters dict, list of required parameter names)
        """
        # MCP inputSchema is a JSON Schema object with type, properties, etc.
        # The registry expects just the properties dict
        if "properties" not in input_schema:
            return {}, []

        # Ensure all parameters have descriptions and types (required by registry)
        parameters = {}
        for param_name, param_info in input_schema["properties"].items():
            # Make a copy to avoid modifying the original
            param_copy = dict(param_info)

            # Add default description if missing
            if "description" not in param_copy:
                param_copy["description"] = f"Parameter: {param_name}"

            # Add default type if missing
            if "type" not in param_copy:
                param_copy["type"] = "string"

            parameters[param_name] = param_copy

        # Extract required parameters from the schema
        # In JSON Schema, "required" is an array of parameter names
        required = input_schema.get("required", [])

        return parameters, required
