"""
Template command handlers for WebSocket communication.
"""

import logging
import bpy
import json
from ...templates.template_wizard import TemplateWizard
from ..utils.response_manager import ResponseManager

# Configure logging
logger = logging.getLogger(__name__)


class TemplateHandlers:
    """Handlers for template-related WebSocket commands."""

    # Create a single shared instance of TemplateWizard
    template_wizard = TemplateWizard()

    # Get a single shared instance of ResponseManager
    response_manager = ResponseManager.get_instance()

    @staticmethod
    def handle_get_template_controls(data):
        """Handle getting template controls"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling get template controls request with message_id: {message_id}")

            # Extract parameters from the request
            template_name = data.get('template_name')

            # Get the template controls
            controls = TemplateHandlers.template_wizard.get_template_controls()

            logger.info(
                f"Template controls retrieved: {len(controls)} controls")

            # Send response with the controls
            TemplateHandlers.response_manager.send_response('template_controls_result', True, {
                "controls": controls,
                "template_name": template_name,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error getting template controls: {e}")
            import traceback
            traceback.print_exc()
            TemplateHandlers.response_manager.send_response('template_controls_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_update_template_control(data):
        """Handle updating a template control value"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling update template control request with message_id: {message_id}")

            # Extract parameters from the request
            template_name = data.get('template_name')
            control_id = data.get('control_id')
            value = data.get('value')

            # Update the control value
            result = TemplateHandlers.template_wizard.update_control_value(
                template_name, control_id, value)

            logger.info(f"Template control update result: {result}")

            # Send response with the result
            TemplateHandlers.response_manager.send_response('update_template_control_result', result.get('success', False), {
                "data": result,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error updating template control: {e}")
            import traceback
            traceback.print_exc()
            TemplateHandlers.response_manager.send_response('update_template_control_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })

    @staticmethod
    def handle_get_template_info(data):
        """Handle getting template information"""
        try:
            message_id = data.get('message_id')
            logger.info(
                f"Handling get template info request with message_id: {message_id}")

            # Extract parameters from the request
            template_name = data.get('template_name')

            # Get the template info
            info = TemplateHandlers.template_wizard.get_template_info(
                template_name)

            logger.info(f"Template info retrieved for {template_name}")

            # Send response with the info
            TemplateHandlers.response_manager.send_response('template_info_result', True, {
                "info": info,
                "template_name": template_name,
                "message_id": message_id
            })

        except Exception as e:
            logger.error(f"Error getting template info: {e}")
            import traceback
            traceback.print_exc()
            TemplateHandlers.response_manager.send_response('template_info_result', False, {
                "message": str(e),
                "message_id": data.get('message_id')
            })
