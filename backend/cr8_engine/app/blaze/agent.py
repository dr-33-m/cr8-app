"""
B.L.A.Z.E Agent - Main Pydantic AI Agent
Processes natural language requests and executes scene manipulations.
"""

import logging
import json
import os
from typing import Dict, Any, Optional
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.toolsets import FunctionToolset
from .context_manager import ContextManager
from .mcp_server import DynamicMCPServer

logger = logging.getLogger(__name__)


class BlazeAgent:
    """Main B.L.A.Z.E agent for natural language scene control"""

    def __init__(self, session_manager, handlers, model_name: str = "anthropic/claude-sonnet-4"):
        """Initialize B.L.A.Z.E agent with OpenRouter"""
        # Initialize logger first
        self.logger = logging.getLogger(__name__)

        self.session_manager = session_manager
        self.handlers = handlers
        self.context_manager = ContextManager()
        self.mcp_server = DynamicMCPServer(session_manager, handlers)

        # Store addon manifests for dynamic toolset
        self.addon_manifests = []
        self.current_username = None

        # Configure OpenRouter using OpenRouterProvider
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            self.logger.error(
                "OPENROUTER_API_KEY not found in environment variables")
            raise ValueError("OPENROUTER_API_KEY is required")

        # Create OpenAI model with OpenRouter provider
        self.model = OpenAIModel(
            model_name,
            provider=OpenRouterProvider(api_key=openrouter_api_key)
        )

        # Initialize Pydantic AI agent with dynamic toolsets
        self.agent = Agent(
            self.model,
            system_prompt=self._get_dynamic_system_prompt()
        )

        # Register dynamic toolset
        self.agent.toolset()(self._build_dynamic_toolset)

        self.logger.info(
            f"B.L.A.Z.E Agent initialized with OpenRouter model: {model_name}")

    def _get_dynamic_system_prompt(self) -> str:
        """Get dynamic system prompt based on current addon capabilities"""
        if not self.addon_manifests:
            return """
You are B.L.A.Z.E (Blender's Artistic Zen Engineer), an intelligent assistant that helps users control 3D scenes in Blender through natural language.

Your capabilities are dynamically determined by the AI-capable addons currently installed in Blender. 

Currently no addons are available. Please ensure Blender is connected and AI-capable addons are installed.
"""

        # Build dynamic system prompt
        return self.mcp_server.build_agent_context(self.addon_manifests)

    def _build_dynamic_toolset(self, ctx: RunContext) -> Optional[FunctionToolset]:
        """Build dynamic toolset based on current addon manifests"""
        try:
            if not self.addon_manifests:
                self.logger.debug("No addon manifests available for toolset")
                return None

            # Create list of tool functions
            tools = []

            for manifest in self.addon_manifests:
                addon_id = manifest.get('addon_id')
                addon_tools = manifest.get('tools', [])

                for tool in addon_tools:
                    tool_name = tool['name']
                    tool_description = tool['description']

                    # Create tool function that calls our MCP server
                    def make_tool_function(aid, tname, desc):
                        async def tool_function(**kwargs) -> str:
                            """Dynamic tool function"""
                            result = await self.mcp_server.execute_addon_command(aid, tname, kwargs)
                            return result

                        tool_function.__name__ = tname
                        tool_function.__doc__ = desc
                        return tool_function

                    # Create the tool function
                    tool_func = make_tool_function(
                        addon_id, tool_name, tool_description)
                    tools.append(tool_func)

                    self.logger.debug(
                        f"Added dynamic tool to toolset: {tool_name}")

            self.logger.info(
                f"Built dynamic toolset with {len(tools)} tools")

            # Return FunctionToolset with all dynamic tools
            return FunctionToolset(tools=tools)

        except Exception as e:
            self.logger.error(f"Error building dynamic toolset: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    async def process_message(self, username: str, message: str,
                              client_type: str = "browser") -> Dict[str, Any]:
        """Process a natural language message from user"""
        try:
            # Store current username for tool access
            self.current_username = username
            self.mcp_server.set_current_username(username)

            # Get current scene context
            scene_context = self.context_manager.get_scene_summary(username)
            self.logger.info(f"Scene context for {username}: {scene_context}")

            # Debug logging for addon manifests
            self.logger.info(f"DEBUG: Agent instance ID: {id(self)}")
            self.logger.info(
                f"DEBUG: addon_manifests length: {len(self.addon_manifests)}")
            self.logger.info(
                f"DEBUG: addon_manifests content: {self.addon_manifests}")

            # Check if we have any capabilities
            if not self.addon_manifests:
                self.logger.warning(
                    f"No addon manifests available for user {username}")
                return {
                    "type": "agent_response",
                    "status": "error",
                    "message": "No AI capabilities are currently available. Please ensure Blender is connected and AI-capable addons are installed.",
                    "context": scene_context
                }

            # Prepare context-aware prompt
            full_message = f"""
CURRENT SCENE CONTEXT: {scene_context}

USER REQUEST: {message}

Please analyze the request and use the appropriate tools to accomplish it. 
If the scene context shows no available elements, let the user know what's currently in the scene.
"""

            # Process with Pydantic AI agent
            result = await self.agent.run(full_message)

            # Return structured response
            return {
                "type": "agent_response",
                "status": "success",
                "message": result.output,
                "context": scene_context
            }

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            return {
                "type": "agent_response",
                "status": "error",
                "message": f"Sorry, I encountered an error: {str(e)}",
                "error": str(e)
            }
        finally:
            # Clear username after processing
            self.current_username = None
            self.mcp_server.current_username = None

    def update_scene_context(self, username: str, template_controls: Dict[str, Any]) -> None:
        """Update scene context when template controls change"""
        self.context_manager.update_template_controls(
            username, template_controls)
        self.logger.info(f"Updated scene context for {username}")

    def update_asset_context(self, username: str, assets: list) -> None:
        """Update asset context when assets change"""
        self.context_manager.update_placed_assets(username, assets)
        self.logger.info(f"Updated asset context for {username}")

    def clear_user_context(self, username: str) -> None:
        """Clear context when user disconnects"""
        self.context_manager.clear_context(username)
        self.logger.info(f"Cleared context for {username}")

    def get_available_tools(self) -> Dict[str, str]:
        """Get available tools for debugging"""
        tools = {}
        for manifest in self.addon_manifests:
            for tool in manifest.get('tools', []):
                tools[tool['name']] = tool.get('description', 'No description')
        return tools

    def handle_registry_update(self, registry_data: Dict[str, Any]) -> None:
        """Handle registry update events from Blender"""
        try:
            available_tools = registry_data.get('available_tools', [])
            total_addons = registry_data.get('total_addons', 0)

            # Debug logging for agent instance
            self.logger.info(
                f"DEBUG: Registry update - Agent instance ID: {id(self)}")
            self.logger.info(
                f"Received registry update: {total_addons} addons, {len(available_tools)} tools")

            # Convert tools to manifests format expected by MCP server
            manifests = []
            addons_processed = set()

            for tool in available_tools:
                addon_id = tool.get('addon_id')
                if addon_id and addon_id not in addons_processed:
                    # Group tools by addon
                    addon_tools = [t for t in available_tools if t.get(
                        'addon_id') == addon_id]

                    manifest = {
                        'addon_id': addon_id,
                        'addon_name': tool.get('addon_name', addon_id),
                        'agent_description': f"Addon {addon_id} provides {len(addon_tools)} tools for scene manipulation",
                        'tools': addon_tools,
                        'context_hints': []
                    }
                    manifests.append(manifest)
                    addons_processed.add(addon_id)

            # Store manifests for dynamic toolset
            self.addon_manifests = manifests
            self.logger.info(
                f"DEBUG: Stored {len(self.addon_manifests)} manifests in agent instance {id(self)}")

            # Update MCP server capabilities
            self.mcp_server.refresh_capabilities(manifests)

            self.logger.info(
                f"Updated system capabilities: {len(manifests)} addons with {len(available_tools)} total tools")

        except Exception as e:
            self.logger.error(f"Error handling registry update: {str(e)}")
