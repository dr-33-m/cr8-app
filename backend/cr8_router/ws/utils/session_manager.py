"""
Session manager for storing and retrieving session data across handlers.
"""

import logging

logger = logging.getLogger(__name__)


class SessionManager:
    """
    Singleton class for managing session data.
    Provides centralized access to username and other session variables.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("Creating new SessionManager instance")
            cls._instance = super(SessionManager, cls).__new__(cls)
            cls._instance.username = None
            # Initialize other session data as needed
        return cls._instance

    @classmethod
    def get_instance(cls):
        """Get the singleton instance of SessionManager"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def set_username(self, username):
        """Set the current username"""
        logger.info(f"Setting session username: {username}")
        self.username = username

    def get_username(self):
        """Get the current username"""
        return self.username
