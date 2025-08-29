"""
FastMCP Server for B.L.A.Z.E Agent
Provides dynamic MCP tools based on registered Blender addons.
"""

import logging
from typing import Dict, Any, Optional, List
from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)


class DynamicMCPServer:
    """Dynamic FastMCP Server for B.L.A.Z.E with addon-based tools"""

    def __init__(self, session_manager, handlers):
        """Initialize B.L.A.Z.E MCP server with dynamic tools"""
        self.session_manager = session_manager
        self.handlers = handlers
        self.server = FastMCP('B.L.A.Z.E Dynamic Controller')
        self.current_username = None  # Will be set by agent
        self.registered_tools = {}  # Track dynamically registered tools
        self.registered_tool_names = set()  # Track tool names for removal
        self.addon_manifests = {}  # Store addon manifests

        self.logger = logging.getLogger(__name__)
        self.logger.info("B.L.A.Z.E Dynamic MCP Server initialized")

    def set_current_username(self, username: str):
        """Set the current username for tool operations"""
        self.current_username = username

    def refresh_capabilities(self, addon_manifests: List[Dict[str, Any]]):
        """Update available tools based on addon manifests"""
        try:
            self.logger.info(
                f"Refreshing capabilities with {len(addon_manifests)} addon manifests")

            # Remove existing tools using proper FastMCP API
            for tool_name in self.registered_tool_names.copy():
                try:
                    self.server.remove_tool(tool_name)
                    self.logger.info(f"Removed tool: {tool_name}")
                except Exception as e:
                    self.logger.warning(
                        f"Could not remove tool {tool_name}: {e}")

            # Clear tracking data
            self.registered_tools.clear()
            self.registered_tool_names.clear()
            self.addon_manifests.clear()

            # Store manifests
            for manifest in addon_manifests:
                addon_id = manifest.get('addon_id')
                if addon_id:
                    self.addon_manifests[addon_id] = manifest

            # Register tools from all manifests
            for manifest in addon_manifests:
                self.register_addon_tools(manifest)

            self.logger.info(
                f"Registered {len(self.registered_tools)} dynamic tools")

        except Exception as e:
            self.logger.error(f"Error refreshing capabilities: {str(e)}")
            import traceback
            traceback.print_exc()

    def register_addon_tools(self, manifest: Dict[str, Any]):
        """Register tools from a single addon manifest"""
        try:
            addon_id = manifest.get('addon_id')
            addon_name = manifest.get('addon_name', addon_id)
            tools = manifest.get('tools', [])

            self.logger.info(
                f"Registering {len(tools)} tools for addon {addon_id}")

            for tool in tools:
                tool_name = tool['name']
                tool_description = tool['description']
                tool_params = tool.get('parameters', [])

                # Create dynamic tool function with proper closure
                def make_dynamic_tool(aid, tname):
                    async def dynamic_tool(**kwargs):
                        return await self.execute_addon_command(aid, tname, kwargs)
                    return dynamic_tool

                # Create the tool function
                dynamic_tool = make_dynamic_tool(addon_id, tool_name)

                # Set function metadata
                dynamic_tool.__name__ = tool_name
                dynamic_tool.__doc__ = tool_description

                # Register the tool with FastMCP
                registered_tool = self.server.tool()(dynamic_tool)

                # Track the tool
                self.registered_tools[tool_name] = {
                    'addon_id': addon_id,
                    'addon_name': addon_name,
                    'function': registered_tool,
                    'description': tool_description,
                    'parameters': tool_params
                }
                self.registered_tool_names.add(tool_name)

                self.logger.info(
                    f"Registered tool: {tool_name} from addon {addon_id}")

        except Exception as e:
            self.logger.error(
                f"Error registering addon tools for {addon_id}: {str(e)}")
            import traceback
            traceback.print_exc()

    def _build_function_signature(self, parameters: List[Dict[str, Any]]) -> str:
        """Build function signature string from parameters"""
        sig_parts = []
        for param in parameters:
            param_name = param['name']
            param_type = param['type']
            is_required = param.get('required', False)

            # Map parameter types to Python types
            type_mapping = {
                'string': 'str',
                'integer': 'int',
                'float': 'float',
                'boolean': 'bool',
                'vector3': 'List[float]',
                'color': 'str',
                'object_name': 'str',
                'material_name': 'str',
                'collection_name': 'str',
                'file_path': 'str',
                'enum': 'str'
            }

            python_type = type_mapping.get(param_type, 'str')

            if is_required:
                sig_parts.append(f"{param_name}: {python_type}")
            else:
                default_value = param.get('default', 'None')
                sig_parts.append(
                    f"{param_name}: {python_type} = {default_value}")

        return f"({', '.join(sig_parts)})"

    async def execute_addon_command(self, addon_id: str, command: str, params: Dict[str, Any]) -> str:
        """Execute command on addon via WebSocket"""
        try:
            if not self.current_username:
                return "Error: No active user session"

            self.logger.info(
                f"Executing {addon_id}.{command} with params: {params}")

            # Send command to Blender via WebSocket
            message = {
                "type": "addon_command",
                "addon_id": addon_id,
                "command": command,
                "params": params,
                "username": self.current_username
            }

            # Get session and send message
            session = self.session_manager.get_session(self.current_username)
            if session and session.blender_socket:
                await session.blender_socket.send_json(message)

                # Wait for response (simplified - in real implementation would need proper response handling)
                # For now, return success message
                return f"Successfully executed {command} on {addon_id}"
            else:
                return f"Error: No Blender connection for user {self.current_username}"

        except Exception as e:
            self.logger.error(f"Error executing addon command: {str(e)}")
            return f"Error executing command: {str(e)}"

    def build_agent_context(self, manifests: List[Dict[str, Any]]) -> str:
        """Generate dynamic system prompt from manifests"""
        try:
            base_prompt = """You are B.L.A.Z.E (Blender's Artistic Zen Engineer), an intelligent assistant that helps users control 3D scenes in Blender through natural language.

Your capabilities are dynamically determined by the AI-capable addons currently installed in Blender.

CURRENT CAPABILITIES:

"""

            if not manifests:
                base_prompt += "No AI-capable addons are currently available. Please install some addons to enable scene control capabilities.\n"
                return base_prompt

            # Add addon descriptions
            for manifest in manifests:
                addon_name = manifest.get(
                    'addon_name', manifest.get('addon_id', 'Unknown'))
                description = manifest.get(
                    'agent_description', 'No description available')
                tools = manifest.get('tools', [])

                base_prompt += f"\n**{addon_name}:**\n"
                base_prompt += f"{description}\n"

                if tools:
                    base_prompt += f"Available tools:\n"
                    for tool in tools:
                        base_prompt += f"- {tool['name']}: {tool['description']}\n"

                # Add context hints if available
                context_hints = manifest.get('context_hints', [])
                if context_hints:
                    base_prompt += f"Usage hints:\n"
                    for hint in context_hints:
                        base_prompt += f"- {hint}\n"

                base_prompt += "\n"

            base_prompt += """
GUIDELINES:
- Be conversational and helpful
- Always use the exact names provided in scene context
- If a request requires capabilities that aren't available, explain what addons might be needed
- If scene elements aren't available, explain what's currently in the scene
- Confirm what you've done after executing commands

Remember: Your capabilities change based on installed addons. Use the available tools to accomplish user requests.
"""

            return base_prompt

        except Exception as e:
            self.logger.error(f"Error building agent context: {str(e)}")
            return "Error building agent context. Using basic capabilities."

    def get_available_tools(self) -> Dict[str, str]:
        """Get list of available tools and their descriptions"""
        tools = {}
        for tool_name, tool_info in self.registered_tools.items():
            tools[tool_name] = tool_info['description']
        return tools
