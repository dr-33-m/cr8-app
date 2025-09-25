"""
B.L.A.Z.E Agent - Main Pydantic AI Agent
Processes natural language requests and executes scene manipulations.
"""

import logging
import json
import os
import uuid
import asyncio
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openrouter import OpenRouterProvider
from pydantic_ai.toolsets import FunctionToolset
from pydantic_ai import BinaryContent
from .context_manager import ContextManager

logger = logging.getLogger(__name__)


class BlazeAgent:
    """Main B.L.A.Z.E agent for natural language scene control"""

    def __init__(self, session_manager, handlers, model_name: str = "qwen/qwen3-coder"):
        """Initialize B.L.A.Z.E agent with OpenRouter"""
        # Initialize logger first
        self.logger = logging.getLogger(__name__)

        self.session_manager = session_manager
        self.handlers = handlers
        self.context_manager = ContextManager()

        # Store addon manifests for dynamic toolset
        self.addon_manifests = []
        self.current_username = None
        
        # Response waiting system for proper error handling
        self.pending_responses = {}  # message_id -> Future
        
        # Screenshot data storage for image analysis
        self.screenshot_data = {}  # username -> screenshot_data

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

        # Register dynamic toolset using decorator
        @self.agent.toolset
        def dynamic_addon_toolset(ctx: RunContext) -> Optional[FunctionToolset]:
            """Build toolset dynamically from current addon manifests"""
            return self._build_dynamic_toolset(ctx)

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

        # Build dynamic system prompt from manifests
        return self._build_agent_context(self.addon_manifests)

    def _build_agent_context(self, manifests: List[Dict[str, Any]]) -> str:
        """Generate dynamic system prompt from manifests"""
        base_prompt = """You are B.L.A.Z.E (Blender's Artistic Zen Engineer), an intelligent assistant that helps users control 3D scenes in Blender through natural language.

Your capabilities are dynamically determined by the AI-capable addons currently installed in Blender.

CURRENT CAPABILITIES:

"""

        # Add addon descriptions using standardized ai_integration structure
        for manifest in manifests:
            ai_integration = manifest['ai_integration']
            addon_info = manifest['addon_info']
            
            addon_name = addon_info.get('name', addon_info.get('id', 'Unknown'))
            description = ai_integration.get('agent_description', 'No description available')
            tools = ai_integration.get('tools', [])
            context_hints = ai_integration.get('context_hints', [])

            base_prompt += f"\n**{addon_name}:**\n"
            base_prompt += f"{description}\n"

            if tools:
                base_prompt += f"Available tools:\n"
                for tool in tools:
                    tool_name = tool['name']
                    tool_description = tool['description']
                    tool_params = tool.get('parameters', [])
                    
                    # Include parameter information in the description
                    param_info = ""
                    if tool_params:
                        required_params = [p['name'] for p in tool_params if p.get('required', True)]
                        optional_params = [p['name'] for p in tool_params if not p.get('required', True)]
                        
                        param_parts = []
                        if required_params:
                            param_parts.append(f"required: {', '.join(required_params)}")
                        if optional_params:
                            param_parts.append(f"optional: {', '.join(optional_params)}")
                        param_info = f" ({'; '.join(param_parts)})"
                    
                    base_prompt += f"- {tool_name}: {tool_description}{param_info}\n"

            # Add context hints if available
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
- Use the EXACT parameter names shown in tool descriptions - these are required and cannot be changed

VISUAL VERIFICATION:
- Use the 'get_viewport_screenshot' tool when:
  * User reports something looks wrong or asks you to check the scene
  * User asks for verification ("does this look right?", "can you check?")
  * You suspect there might be a visual issue with positioning or appearance
  * Debugging spatial relationships or object placement
  * User asks you to show them what the scene looks like
- Screenshots help you see what the user sees and provide better assistance

Remember: Your capabilities change based on installed addons. Use the available tools to accomplish user requests.
"""

        return base_prompt

    async def execute_addon_command_direct(self, addon_id: str, command: str, params: Dict[str, Any]):
        """Execute command on addon via WebSocket with response waiting and error handling"""
        try:
            if not self.current_username:
                raise ModelRetry("No active user session available")

            self.logger.info(f"Executing {addon_id}.{command} with params: {params}")

            # Send command and wait for response
            response = await self._send_command_and_wait_response(addon_id, command, params)
            
            # Parse response status
            if response.get('status') == 'error':
                error_msg = response.get('message', 'Unknown error occurred')
                self.logger.error(f"Command {command} failed: {error_msg}")
                raise ModelRetry(f"Command {command} failed: {error_msg}")
            elif response.get('status') == 'success':
                success_msg = response.get('message', 'Command completed')
                self.logger.info(f"Command {command} succeeded: {success_msg}")
                
                # Store screenshot data for later processing if present
                response_data = response.get('data', {})
                if 'image_data' in response_data and 'media_type' in response_data:
                    # Store screenshot data in session for image analysis
                    self._store_screenshot_data(response_data)
                    width = response_data.get('width', 'unknown')
                    height = response_data.get('height', 'unknown')
                    self.logger.info(f"Stored screenshot data for analysis ({width}x{height})")
                
                # Trigger scene context refresh after successful command execution
                await self._refresh_scene_context_universal(self.current_username)
                
                # Always return simple string response (never BinaryContent)
                return f"Successfully executed {command}: {success_msg}"
            else:
                raise ModelRetry(f"Unexpected response from {command}: {response}")
                
        except ModelRetry:
            raise  # Re-raise ModelRetry for Pydantic AI to handle
        except Exception as e:
            self.logger.error(f"Error executing addon command: {str(e)}")
            raise ModelRetry(f"Error executing {command}: {str(e)}")


    async def _send_command_and_wait_response(self, addon_id: str, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send command via WebSocket and wait for response"""
        # Create unique message ID
        message_id = str(uuid.uuid4())
        
        # Set up response waiting
        response_future = asyncio.Future()
        self.pending_responses[message_id] = response_future
        
        try:
            # Create command message
            message = {
                "type": "addon_command",
                "addon_id": addon_id,
                "command": command,
                "params": params,
                "username": self.current_username,
                "message_id": message_id
            }
            
            # Send command
            session = self.session_manager.get_session(self.current_username)
            if not session or not session.blender_socket:
                raise Exception("No Blender connection available")
                
            await session.blender_socket.send_json(message)
            self.logger.debug(f"Sent command {command} with message_id {message_id}")
            
            # Wait for response (no timeout - Blender will always respond)
            response = await response_future
            
            return response
            
        finally:
            # Cleanup pending response
            self.pending_responses.pop(message_id, None)


    def handle_command_response(self, message_id: str, response_data: Dict[str, Any]):
        """Handle incoming command responses from WebSocket"""
        try:
            if message_id in self.pending_responses:
                future = self.pending_responses[message_id]
                if not future.done():
                    future.set_result(response_data)
                    self.logger.debug(f"Resolved response for message_id {message_id}")
                else:
                    self.logger.warning(f"Response future for {message_id} already resolved")
            else:
                self.logger.warning(f"No pending response found for message_id {message_id}")
        except Exception as e:
            self.logger.error(f"Error handling command response: {str(e)}")

    def _store_screenshot_data(self, response_data: Dict[str, Any]) -> None:
        """Store screenshot data for image analysis"""
        try:
            if not self.current_username:
                self.logger.warning("No current username to store screenshot data")
                return
                
            import base64
            
            image_data_b64 = response_data.get('image_data')
            media_type = response_data.get('media_type', 'image/png')
            width = response_data.get('width', 'unknown')
            height = response_data.get('height', 'unknown')
            
            if image_data_b64:
                # Convert base64 to binary data for BinaryContent
                image_bytes = base64.b64decode(image_data_b64)
                
                # Store screenshot data for this user
                self.screenshot_data[self.current_username] = {
                    'image_bytes': image_bytes,
                    'media_type': media_type,
                    'width': width,
                    'height': height,
                    'timestamp': time.time()
                }
                
                self.logger.debug(f"Stored screenshot data for {self.current_username}: {width}x{height}")
            else:
                self.logger.warning("No image data in response_data")
                
        except Exception as e:
            self.logger.error(f"Error storing screenshot data: {str(e)}")

    def _get_and_clear_screenshot_data(self, username: str) -> Optional[Dict[str, Any]]:
        """Get screenshot data for user and clear it from storage"""
        try:
            screenshot_data = self.screenshot_data.pop(username, None)
            if screenshot_data:
                self.logger.debug(f"Retrieved screenshot data for {username}")
            return screenshot_data
        except Exception as e:
            self.logger.error(f"Error retrieving screenshot data: {str(e)}")
            return None

    async def _refresh_scene_context_universal(self, username: str) -> None:
        """Universal context refresh by calling list_scene_objects from any available addon"""
        try:
            # Find any addon that provides list_scene_objects using standardized ai_integration structure
            list_objects_addon = None
            for manifest in self.addon_manifests:
                tools = manifest['ai_integration']['tools']
                
                if any(tool.get('name') == 'list_scene_objects' for tool in tools):
                    list_objects_addon = manifest['addon_info']['id']
                    break
            
            if not list_objects_addon:
                self.logger.warning("No addon provides list_scene_objects - cannot refresh context")
                return
                
            # Execute list_scene_objects to get current scene state
            list_message = {
                "type": "addon_command",
                "addon_id": list_objects_addon,
                "command": "list_scene_objects",
                "params": {},
                "username": username,
                "message_id": str(uuid.uuid4())
            }
            
            session = self.session_manager.get_session(username)
            if session and session.blender_socket:
                await session.blender_socket.send_json(list_message)
                self.logger.info(f"Triggered scene context refresh for {username}")
            
        except Exception as e:
            self.logger.error(f"Error refreshing scene context: {str(e)}")

    def _build_dynamic_toolset(self, ctx: RunContext) -> Optional[FunctionToolset]:
        """Build dynamic toolset with proper parameter schemas from addon manifests"""
        try:
            if not self.addon_manifests:
                self.logger.debug("No addon manifests available for toolset")
                return None

            toolset = FunctionToolset()

            for manifest in self.addon_manifests:
                addon_id = manifest['addon_info']['id']
                tools = manifest['ai_integration']['tools']

                for tool in tools:
                    tool_name = tool['name']
                    tool_description = tool['description']
                    tool_params = tool.get('parameters', [])

                    # Create dynamic function with proper parameter signature
                    dynamic_tool = self._create_dynamic_tool_function(
                        addon_id, tool_name, tool_description, tool_params
                    )

                    # Add function to toolset with retry configuration
                    toolset.add_function(dynamic_tool, name=tool_name, retries=2)

                    self.logger.debug(
                        f"Added dynamic tool to toolset: {tool_name} with {len(tool_params)} parameters")

            self.logger.info(
                f"Built dynamic toolset with {len(toolset.tools)} tools")

            return toolset

        except Exception as e:
            self.logger.error(f"Error building dynamic toolset: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _create_dynamic_tool_function(self, addon_id: str, tool_name: str, tool_description: str, tool_params: List[Dict[str, Any]]):
        """Create a dynamic function with proper parameter signatures"""
        
        # Sort parameters: required first, then optional (Python syntax requirement)
        required_params = [p for p in tool_params if p.get('required', True)]
        optional_params = [p for p in tool_params if not p.get('required', True)]
        sorted_params = required_params + optional_params
        
        # Build parameter collection code for the function body
        param_collection_code = []
        param_signature_parts = []
        
        for param in sorted_params:
            param_name = param['name']
            is_required = param.get('required', True)
            default_value = param.get('default')
            
            param_collection_code.append(f"'{param_name}': {param_name}")
            
            # Build function signature part
            if is_required:
                param_signature_parts.append(param_name)
            else:
                # Handle defaults for optional parameters
                if default_value is not None:
                    param_signature_parts.append(f"{param_name}={repr(default_value)}")
                else:
                    param_signature_parts.append(f"{param_name}=None")

        # Create function code with proper parameter signature
        signature_str = ', '.join(param_signature_parts) if param_signature_parts else ''
        param_dict_code = '{' + ', '.join(param_collection_code) + '}' if param_collection_code else '{}'
        
        # Generate the complete function code
        function_code = f'''
async def {tool_name}({signature_str}):
    """
    {tool_description}
    """
    # Collect parameters into dict, filtering out None values
    all_params = {param_dict_code}
    filtered_params = {{k: v for k, v in all_params.items() if v is not None}}
    
    return await self.execute_addon_command_direct('{addon_id}', '{tool_name}', filtered_params)
'''
        
        # Create namespace and execute function definition
        namespace = {'self': self}
        
        exec(function_code, namespace)
        dynamic_function = namespace[tool_name]
        
        self.logger.debug(f"Created function {tool_name} with signature: {signature_str}")
        
        return dynamic_function

    async def process_message(self, username: str, message: str,
                              client_type: str = "browser") -> Dict[str, Any]:
        """Process a natural language message from user"""
        try:
            # Store current username for tool access
            self.current_username = username

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

            # Process with Pydantic AI agent and store result for message history
            result = await self.agent.run(full_message)

            # Check if screenshot was captured during this conversation
            screenshot_data = self._get_and_clear_screenshot_data(username)
            
            if screenshot_data:
                # Perform image analysis with full conversation context
                try:
                    self.logger.info(f"Performing image analysis with conversation context")
                    
                    analysis_prompt = f"""ORIGINAL USER REQUEST: {message}

CURRENT SCENE CONTEXT: {scene_context}

SCREENSHOT ANALYSIS: I have captured a screenshot of the current 3D viewport. Please analyze this image and verify if the requested action was completed correctly. Look for:

- Object positioning and placement relative to the user's request
- Scene composition and layout
- Visual correctness of any operations performed
- Any issues or improvements that could be made

Provide a brief analysis of what you see and whether it matches what the user requested. Be specific about what objects you can see and their arrangement."""

                    # Use proper Pydantic AI pattern with BinaryContent as input and message history
                    analysis_result = await self.agent.run(
                        [analysis_prompt, BinaryContent(
                            data=screenshot_data['image_bytes'], 
                            media_type=screenshot_data['media_type']
                        )],
                        message_history=result.all_messages()
                    )
                    
                    # Combine original response with image analysis
                    combined_response = f"{result.output}\n\n📸 **Visual Verification:** {analysis_result.output}"
                    
                    self.logger.info(f"Successfully completed image analysis for {username}")
                    
                    return {
                        "type": "agent_response",
                        "status": "success",
                        "message": combined_response,
                        "context": scene_context
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error during image analysis: {str(e)}")
                    # Fall back to original response if image analysis fails
                    fallback_response = f"{result.output}\n\n📸 **Visual Verification:** Screenshot captured but analysis failed: {str(e)}"
                    
                    return {
                        "type": "agent_response",
                        "status": "success",
                        "message": fallback_response,
                        "context": scene_context
                    }

            # Return original response if no screenshot was captured
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


    def clear_user_context(self, username: str) -> None:
        """Clear context when user disconnects"""
        self.context_manager.clear_context(username)
        self.logger.info(f"Cleared context for {username}")

    def get_available_tools(self) -> Dict[str, str]:
        """Get available tools for debugging"""
        tools = {}
        for manifest in self.addon_manifests:
            for tool in manifest['ai_integration']['tools']:
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

            # Convert tools to standardized ai_integration manifests format
            manifests = []
            addons_processed = set()

            for tool in available_tools:
                addon_id = tool.get('addon_id')
                if addon_id and addon_id not in addons_processed:
                    # Group tools by addon
                    addon_tools = [t for t in available_tools if t.get(
                        'addon_id') == addon_id]

                    # Create manifest in standardized ai_integration format
                    manifest = {
                        'addon_info': {
                            'id': addon_id,
                            'name': tool.get('addon_name', addon_id)
                        },
                        'ai_integration': {
                            'agent_description': f"Addon {addon_id} provides {len(addon_tools)} tools for scene manipulation",
                            'tools': addon_tools,
                            'context_hints': []
                        }
                    }
                    manifests.append(manifest)
                    addons_processed.add(addon_id)

            # Store manifests for dynamic toolset
            self.addon_manifests = manifests
            self.logger.info(
                f"DEBUG: Stored {len(self.addon_manifests)} manifests in agent instance {id(self)}")

            self.logger.info(
                f"Updated system capabilities: {len(manifests)} addons with {len(available_tools)} total tools")

        except Exception as e:
            self.logger.error(f"Error handling registry update: {str(e)}")
