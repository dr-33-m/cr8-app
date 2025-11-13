"""
Message Processor - Handles message processing orchestration
Extracts scene context, builds prompts, and orchestrates Pydantic AI agent execution.
"""

import logging
from typing import Dict, Any, Optional
from pydantic_ai import BinaryContent

logger = logging.getLogger(__name__)


class MessageProcessor:
    """Handles message processing and Pydantic AI agent orchestration"""

    def __init__(self, agent_instance):
        """Initialize message processor with agent reference"""
        self.agent_instance = agent_instance
        self.logger = logging.getLogger(__name__)

    async def process_message(
        self,
        username: str,
        message: str,
        client_type: str = "browser",
        context: Optional[Dict[str, Any]] = None,
        deps: Optional[Dict[str, Any]] = None,
        route: str = 'agent'
    ) -> Dict[str, Any]:
        """Process a natural language message from user"""
        try:
            # Store current username and route for tool access
            self.agent_instance.current_username = username
            self.agent_instance.current_route = route

            # Extract and format scene context
            scene_context = self._extract_scene_context(context)
            self.logger.info(f"Scene context for {username}: {scene_context}")

            # Initialize deps if needed and add inbox_items for tool access
            if deps is None:
                deps = {}
            
            # Add inbox_items to deps so tools can access them via RunContext
            if context and 'inbox_items' in context:
                deps['inbox_items'] = context['inbox_items']
                self.logger.debug(f"Added {len(context['inbox_items'])} inbox items to deps")
            
            # Add browser_namespace and agent_instance to deps for local tools
            deps['browser_namespace'] = self.agent_instance.browser_namespace
            deps['agent_instance'] = self.agent_instance

            # Get registry data from deps
            addon_registry = deps.get('addon_registry') if deps else None

            # Check if we have any capabilities
            if not addon_registry or not addon_registry.get('available_tools'):
                self.logger.warning(f"No addon registry available for user {username}")
                return self._build_error_response(
                    'BLENDER_DISCONNECTED',
                    'No addon registry available'
                )

            # Extract and format inbox context
            inbox_section = self._extract_inbox_context(context)

            # Build full message prompt with clear separation
            full_message = self._build_full_prompt(message, scene_context, inbox_section)

            # Process with Pydantic AI agent
            result = await self.agent_instance.agent.run(full_message, deps=deps)

            # Check if screenshot was captured and perform image analysis
            response = await self._handle_screenshot_analysis(
                username, message, scene_context, result
            )

            return response

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            error_response = self._build_error_response('EXECUTION_FAILED', str(e))
            
            # Emit error to frontend so user knows something failed
            try:
                await self.agent_instance.browser_namespace.send_agent_error(username, error_response)
            except Exception as emit_error:
                self.logger.error(f"Failed to emit error to frontend: {str(emit_error)}")
            
            return error_response

        finally:
            # Clear username and route after processing
            self.agent_instance.current_username = None
            self.agent_instance.current_route = 'agent'

    def _extract_scene_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Extract and format scene context from context dict"""
        try:
            scene_objects = context.get('scene_objects', []) if context else []
            if scene_objects:
                object_names = [obj.get('name', 'Unknown') for obj in scene_objects]
                return f"Scene objects: {', '.join(object_names)}"
            else:
                return "Empty scene"
        except Exception as e:
            self.logger.error(f"Error extracting scene context: {str(e)}")
            return "Scene context unavailable"

    def _extract_inbox_context(self, context: Optional[Dict[str, Any]]) -> str:
        """Extract and format inbox context from context dict"""
        try:
            inbox_context = context.get('inbox_items', []) if context else []

            if inbox_context and len(inbox_context) > 0:
                inbox_names = [
                    f"{item.get('name', 'Unknown')} ({item.get('type', 'asset')})"
                    for item in inbox_context
                ]
                return f"\nINBOX ITEMS (not yet in scene): {len(inbox_context)} assets ready to process:\n{', '.join(inbox_names)}"
            else:
                return ""
        except Exception as e:
            self.logger.error(f"Error extracting inbox context: {str(e)}")
            return ""

    def _build_full_prompt(
        self,
        message: str,
        scene_context: str,
        inbox_section: str
    ) -> str:
        """Build full message prompt with clear separation between contexts"""
        return f"""
CURRENT SCENE STATE (cached - call list_scene_objects() for fresh data):
{scene_context}
{inbox_section}

USER REQUEST: {message}

Note: The scene context above may be stale. Call list_scene_objects() to get the current scene state, especially after making changes or when you need to verify what's actually in the scene. The inbox items are not yet in the scene - use process_inbox_assets() if you want to download and import them.
"""

    async def _handle_screenshot_analysis(
        self,
        username: str,
        message: str,
        scene_context: str,
        result: Any
    ) -> Dict[str, Any]:
        """Handle screenshot capture and image analysis if available"""
        try:
            # Check if screenshot was captured during this conversation
            screenshot_data = self.agent_instance.screenshot_manager.get_and_clear_screenshot(
                username
            )

            if screenshot_data:
                # Perform image analysis with full conversation context
                return await self._perform_image_analysis(
                    message, scene_context, result, screenshot_data
                )
            else:
                # No screenshot, return standard response
                return {
                    'status': 'success',
                    'message': result.output,
                    'context': scene_context
                }

        except Exception as e:
            self.logger.error(f"Error handling screenshot analysis: {str(e)}")
            # Return original response if screenshot handling fails
            return {
                'status': 'success',
                'message': result.output,
                'context': scene_context
            }

    async def _perform_image_analysis(
        self,
        message: str,
        scene_context: str,
        result: Any,
        screenshot_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform image analysis on captured screenshot"""
        try:
            self.logger.info("Performing image analysis with conversation context")

            analysis_prompt = self._build_analysis_prompt(message, scene_context)

            # Use proper Pydantic AI pattern with BinaryContent
            analysis_result = await self.agent_instance.agent.run(
                [
                    analysis_prompt,
                    BinaryContent(
                        data=screenshot_data['image_bytes'],
                        media_type=screenshot_data['media_type']
                    )
                ],
                message_history=result.all_messages()
            )

            # Combine original response with image analysis
            combined_response = (
                f"{result.output}\n\n📸 **Visual Verification:** {analysis_result.output}"
            )

            self.logger.info("Successfully completed image analysis")

            return {
                'status': 'success',
                'message': combined_response,
                'context': scene_context
            }

        except Exception as e:
            self.logger.error(f"Error during image analysis: {str(e)}")
            # Fall back to original response if image analysis fails
            fallback_response = (
                f"{result.output}\n\n📸 **Visual Verification:** "
                f"Screenshot captured but analysis failed: {str(e)}"
            )

            return {
                'status': 'success',
                'message': fallback_response,
                'context': scene_context
            }

    def _build_analysis_prompt(self, message: str, scene_context: str) -> str:
        """Build prompt for image analysis"""
        return f"""ORIGINAL USER REQUEST: {message}

CURRENT SCENE CONTEXT: {scene_context}

SCREENSHOT ANALYSIS: I have captured a screenshot of the current 3D viewport. Please analyze this image and verify if the requested action was completed correctly. Look for:

- Object positioning and placement relative to the user's request
- Scene composition and layout
- Visual correctness of any operations performed
- Any issues or improvements that could be made

Provide a brief analysis of what you see and whether it matches what the user requested. Be specific about what objects you can see and their arrangement."""

    def _build_error_response(self, error_code: str, error_message: str) -> Dict[str, Any]:
        """Build standardized error response"""
        from app.lib import translate_error

        error_info = translate_error(error_code, error_message)

        return {
            'status': 'error',
            'error_code': error_code,
            'user_message': error_info['user_message'],
            'technical_message': error_message,
            'recovery_suggestions': error_info['recovery_suggestions']
        }
