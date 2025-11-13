"""
Registry update handlers for Blender namespace.
"""

import logging
from typing import Dict, Any


logger = logging.getLogger(__name__)


class RegistryHandlersMixin:
    """Mixin providing registry update handling for BlenderNamespace."""

    async def on_registry_update(self, sid: str, data: Dict[str, Any]):
        """
        Handle registry update events from Blender AI Router.

        Args:
            sid: Socket.IO session ID
            data: Registry update data
        """
        try:
            session = await self.get_session(sid)
            if not session:
                self.logger.error(f"No session found for sid {sid}")
                return

            username = session['username']
            browser_sid = session['browser_sid']

            self.logger.info(f"Received registry update from Blender for {username}")

            # Store registry in Blender session (for persistence across server restarts)
            session['addon_registry'] = data
            await self.save_session(sid, session)
            self.logger.info(f"Stored registry data in Blender session for {username}")

            # Get browser session to store registry data
            browser_namespace = self.server.namespace_handlers.get('/browser')
            if browser_namespace:
                browser_session = await browser_namespace.get_session(browser_sid)
                if browser_session:
                    # Store registry data in browser session (as serializable dict)
                    browser_session['addon_registry'] = data
                    await browser_namespace.save_session(browser_sid, browser_session)
                    self.logger.info(f"Stored registry data in browser session for {username}")

            # Send acknowledgment back to Blender
            await self.emit('registry_update_ack', {
                'status': 'processed',
                'message': 'Registry update processed successfully'
            }, to=sid)

        except Exception as e:
            self.logger.error(f"Error handling registry update: {str(e)}")
            await self.emit('registry_update_ack', {
                'status': 'error',
                'message': f'Failed to process registry update: {str(e)}'
            }, to=sid)
