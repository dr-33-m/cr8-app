"""
B.L.A.Z.E Agent - Main Pydantic AI Agent
Processes natural language requests and executes scene manipulations.
"""

import logging
import json
import os
import asyncio
import time
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, List
from pydantic_ai import Agent, RunContext, ModelRetry
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.toolsets import FunctionToolset
from pydantic_ai import BinaryContent
from .providers import create_provider_from_env, ProviderConfig
from app.lib import (
    MessageType,
    create_success_response,
    create_error_response,
    translate_error,
    generate_message_id,
)

logger = logging.getLogger(__name__)


class BlazeAgent:
    """Main B.L.A.Z.E agent for natural language scene control"""

    def __init__(self, browser_namespace, blender_namespace):
        """Initialize B.L.A.Z.E agent with Socket.IO namespaces"""
        # Initialize logger first
        self.logger = logging.getLogger(__name__)

        self.browser_namespace = browser_namespace
        self.blender_namespace = blender_namespace

        # Current username and route for tool execution context
        self.current_username = None
        self.current_route = 'agent'  # Default route for agent-initiated commands
        
        # Response waiting system for proper error handling
        self.pending_responses = {}  # message_id -> Future
        
        # Screenshot data storage for image analysis
        self.screenshot_data = {}  # username -> screenshot_data

        # Create AI model using the new provider system
        try:
            self.model = create_provider_from_env()
        except Exception as e:
            self.logger.error(f"Failed to create AI provider: {e}")
            raise

        # Initialize Pydantic AI agent with dynamic toolsets
        # Agent uses Dict[str, Any] as deps_type to receive registry data
        self.agent = Agent(
            self.model,
            deps_type=Dict[str, Any],
            system_prompt="You are B.L.A.Z.E (Blender's Artistic Zen Engineer), an intelligent assistant that helps users control 3D scenes in Blender through natural language."
        )

        # Register dynamic toolset using decorator
        @self.agent.toolset
        def dynamic_addon_toolset(ctx: RunContext[Dict[str, Any]]) -> Optional[FunctionToolset]:
            """Build toolset dynamically from registry data in context"""
            # Get registry data from dependencies
            registry_data = ctx.deps.get('addon_registry') if ctx.deps else None
            if not registry_data:
                self.logger.debug("No registry data in context")
                return None
            
            return self._build_dynamic_toolset_from_registry(registry_data)

        # Get provider info for logging
        provider_type = os.getenv("AI_PROVIDER", "openrouter")
        model_name = os.getenv("AI_MODEL_NAME")
        self.logger.info(
            f"B.L.A.Z.E Agent initialized with {provider_type} provider and model: {model_name}")


    async def execute_addon_command_direct(self, addon_id: str, command: str, params: Dict[str, Any]):
        """Execute command on addon via WebSocket with response waiting and error handling"""
        try:
            if not self.current_username:
                raise ModelRetry("No active user session available")

            self.logger.info(f"Executing {addon_id}.{command} with params: {params}")

            # Send command and wait for response
            response = await self._send_command_and_wait_response(addon_id, command, params)
            
            # Parse response status from SocketMessage payload
            payload = response.get('payload', {})
            if payload.get('status') == 'error':
                # Extract error details from payload
                error_data = payload.get('data', {})
                error_msg = error_data.get('message', 'Unknown error occurred')
                self.logger.error(f"Command {command} failed: {error_msg}")
                raise ModelRetry(f"Command {command} failed: {error_msg}")
            elif payload.get('status') == 'success':
                # Extract success details from payload
                success_data = payload.get('data', {})
                success_msg = success_data.get('message', 'Command completed')
                self.logger.info(f"Command {command} succeeded: {success_msg}")
                
                # Store screenshot data for later processing if present
                if 'image_data' in success_data and 'media_type' in success_data:
                    # Store screenshot data in session for image analysis
                    self._store_screenshot_data(success_data)
                    width = success_data.get('width', 'unknown')
                    height = success_data.get('height', 'unknown')
                    self.logger.info(f"Stored screenshot data for analysis ({width}x{height})")
                
                # Return the actual response data for parsing by caller
                return response
            else:
                raise ModelRetry(f"Unexpected response from {command}: {response}")
                
        except ModelRetry:
            raise  # Re-raise ModelRetry for Pydantic AI to handle
        except Exception as e:
            self.logger.error(f"Error executing addon command: {str(e)}")
            raise ModelRetry(f"Error executing {command}: {str(e)}")


    async def _send_command_and_wait_response(self, addon_id: str, command: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send command via unified routing system and wait for response"""
        # Create unique message ID using standardized utility
        message_id = generate_message_id()
        
        # Set up response waiting
        response_future = asyncio.Future()
        self.pending_responses[message_id] = response_future
        
        try:
            # Create command message
            command_data = {
                "type": "addon_command",
                "addon_id": addon_id,
                "command": command,
                "params": params,
                "message_id": message_id,
                "metadata": {
                    "route": self.current_route
                }
            }
            
            # Validate username
            if not self.current_username:
                raise Exception("No active username")
            
            # Use unified send_command_to_blender() method with preserved route
            # This ensures all commands (direct or agent-initiated) use the same routing
            # Route is preserved from the original frontend request
            success = await self.blender_namespace.send_command_to_blender(
                self.current_username, 
                command_data,
                route=self.current_route
            )
            
            if not success:
                raise Exception(f"Failed to send command {command} to Blender")
            
            self.logger.debug(f"Sent command {command} with message_id {message_id} via unified routing")
            
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


    def _build_dynamic_toolset_from_registry(self, registry_data: Dict[str, Any]) -> Optional[FunctionToolset]:
        """Build dynamic toolset from registry data"""
        try:
            available_tools = registry_data.get('available_tools', [])
            if not available_tools:
                self.logger.debug("No tools in registry data")
                return None

            # Convert tools to manifests format
            manifests = []
            addons_processed = set()

            for tool in available_tools:
                addon_id = tool.get('addon_id')
                if addon_id and addon_id not in addons_processed:
                    # Group tools by addon
                    addon_tools = [t for t in available_tools if t.get('addon_id') == addon_id]

                    # Create manifest
                    manifest = {
                        'addon_info': {
                            'id': addon_id,
                            'name': tool.get('addon_name', addon_id)
                        },
                        'ai_integration': {
                            'tools': addon_tools
                        }
                    }
                    manifests.append(manifest)
                    addons_processed.add(addon_id)

            # Build toolset from manifests
            toolset = FunctionToolset()
            added_tools = set()  # Track tool names to avoid duplicates

            for manifest in manifests:
                addon_id = manifest['addon_info']['id']
                tools = manifest['ai_integration']['tools']

                for tool in tools:
                    tool_name = tool['name']
                    
                    # Skip if tool already added (deduplication)
                    if tool_name in added_tools:
                        self.logger.warning(
                            f"Skipping duplicate tool '{tool_name}' from addon '{addon_id}'")
                        continue
                    
                    tool_description = tool['description']
                    tool_params = tool.get('parameters', [])

                    # Create dynamic function with proper parameter signature
                    dynamic_tool = self._create_dynamic_tool_function(
                        addon_id, tool_name, tool_description, tool_params
                    )

                    # Add function to toolset with retry configuration
                    toolset.add_function(dynamic_tool, name=tool_name, retries=2)
                    added_tools.add(tool_name)

                    self.logger.debug(
                        f"Added dynamic tool to toolset: {tool_name} with {len(tool_params)} parameters")

            self.logger.info(
                f"Built dynamic toolset with {len(toolset.tools)} tools from registry")

            return toolset

        except Exception as e:
            self.logger.error(f"Error building dynamic toolset from registry: {str(e)}")
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
                              client_type: str = "browser", 
                              context: Optional[Dict[str, Any]] = None,
                              deps: Optional[Dict[str, Any]] = None,
                              route: str = 'agent') -> Dict[str, Any]:
        """Process a natural language message from user"""
        try:
            # Store current username and route for tool access
            self.current_username = username
            self.current_route = route  # Store route for command forwarding

            # Get scene context from passed context instead of ContextManager
            scene_objects = context.get('scene_objects', []) if context else []
            if scene_objects:
                object_names = [obj.get('name', 'Unknown') for obj in scene_objects]
                scene_context = f"Scene objects: {', '.join(object_names)}"
            else:
                scene_context = "Empty scene"
            self.logger.info(f"Scene context for {username}: {scene_context}")

            # Get registry data from deps
            addon_registry = deps.get('addon_registry') if deps else None
            
            # Check if we have any capabilities
            if not addon_registry or not addon_registry.get('available_tools'):
                self.logger.warning(f"No addon registry available for user {username}")
                
                # Use error translation for user-friendly message
                error_info = translate_error(
                    'BLENDER_DISCONNECTED',
                    'No addon registry available'
                )
                
                # Return raw error data - backend will wrap in SocketMessage
                return {
                    'status': 'error',
                    'error_code': 'BLENDER_DISCONNECTED',
                    'user_message': error_info['user_message'],
                    'technical_message': 'No addon registry available',
                    'recovery_suggestions': error_info['recovery_suggestions']
                }

            # Extract inbox context from the passed context
            inbox_context = context.get('inbox_items', []) if context else []
            
            # Build clear, separated context for intelligent agent decision making
            inbox_section = ""
            if inbox_context and len(inbox_context) > 0:
                inbox_names = [f"{item.get('name', 'Unknown')} ({item.get('type', 'asset')})" for item in inbox_context]
                inbox_section = f"\nINBOX ITEMS (not yet in scene): {len(inbox_context)} assets ready to process:\n{', '.join(inbox_names)}"

            # Prepare context-aware prompt with clear separation between current scene and inbox
            full_message = f"""
CURRENT SCENE STATE (cached - call list_scene_objects() for fresh data):
{scene_context}
{inbox_section}

USER REQUEST: {message}

Note: The scene context above may be stale. Call list_scene_objects() to get the current scene state, especially after making changes or when you need to verify what's actually in the scene. The inbox items are not yet in the scene - use process_inbox_assets() if you want to download and import them.
"""

            # Process with Pydantic AI agent, passing registry as dependencies
            result = await self.agent.run(full_message, deps=deps)

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
                    
                    # Return raw data with image analysis - backend will wrap in SocketMessage
                    return {
                        'status': 'success',
                        'message': combined_response,
                        'context': scene_context
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error during image analysis: {str(e)}")
                    # Fall back to original response if image analysis fails
                    fallback_response = f"{result.output}\n\n📸 **Visual Verification:** Screenshot captured but analysis failed: {str(e)}"
                    
                    # Return raw data - backend will wrap in SocketMessage
                    return {
                        'status': 'success',
                        'message': fallback_response,
                        'context': scene_context
                    }

            # Return raw data - backend will wrap in SocketMessage
            return {
                'status': 'success',
                'message': result.output,
                'context': scene_context
            }

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            
            # Use error translation for user-friendly message
            error_info = translate_error(
                'EXECUTION_FAILED',
                str(e)
            )
            
            # Return raw error data - backend will wrap in SocketMessage
            return {
                'status': 'error',
                'error_code': 'EXECUTION_FAILED',
                'user_message': error_info['user_message'],
                'technical_message': str(e),
                'recovery_suggestions': error_info['recovery_suggestions']
            }
        finally:
            # Clear username and route after processing
            self.current_username = None
            self.current_route = 'agent'  # Reset to default


    def clear_user_context(self, username: str) -> None:
        """Clear context when user disconnects"""
        self.logger.info(f"Cleared context for {username}")
