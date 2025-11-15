"""
AI Addon Registry - Manages discovery and validation of AI-capable addons.
Main orchestrator that coordinates addon scanning, loading, and registration.
"""

import logging
from pathlib import Path

from .manifest import AddonManifest, load_manifest_file, validate_manifest
from .discovery import discover_addons, load_addon_handlers


class AIAddonRegistry:
    """Registry for managing AI-capable addons"""

    def __init__(self):
        """Initialize the addon registry"""
        self.registered_addons: dict = {}
        self.addon_handlers: dict = {}
        self.logger = logging.getLogger(__name__)

        # Initialize registry
        self.scan_addons()

    def scan_addons(self) -> list:
        """
        Discover and load addon manifests from Blender addons directory.
        
        Returns:
            List of discovered AddonManifest objects
        """
        self.logger.info("Scanning for AI-capable addons...")

        # Create manifest loader with AddonManifest class
        def load_manifest(addon_path: Path, manifest_path: Path):
            return load_manifest_file(
                manifest_path, addon_path, AddonManifest
            )

        # Discover addons using scanner
        discovered_addons = discover_addons(load_manifest)

        # Register each discovered addon
        for manifest in discovered_addons:
            self.register_addon(manifest.addon_id, manifest)

        self.logger.info(
            f"Discovered {len(discovered_addons)} AI-capable addons"
        )
        return discovered_addons

    def validate_manifest(self, manifest: dict) -> bool:
        """
        Validate manifest format and requirements.
        
        Delegates to the specialized manifest validator module.
        
        Args:
            manifest: Manifest dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Delegate to specialized validator
            return validate_manifest(manifest)
        except Exception as e:
            self.logger.error(f"Manifest validation error: {str(e)}")
            return False

    def register_addon(self, addon_id: str, manifest: AddonManifest) -> bool:
        """
        Register addon in the system.
        
        Args:
            addon_id: Unique identifier for the addon
            manifest: AddonManifest object
            
        Returns:
            True if registration successful, False otherwise
        """
        try:
            if not manifest.is_valid:
                self.logger.error(f"Cannot register invalid addon: {addon_id}")
                return False

            # Check for conflicts
            if addon_id in self.registered_addons:
                self.logger.warning(
                    f"Addon {addon_id} already registered, updating..."
                )

            # Store manifest
            self.registered_addons[addon_id] = manifest

            # Try to load command handlers from the addon
            handlers = load_addon_handlers(addon_id, manifest)
            if handlers:
                self.addon_handlers[addon_id] = handlers

            self.logger.info(f"Successfully registered addon: {addon_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering addon {addon_id}: {str(e)}")
            return False

    def unregister_addon(self, addon_id: str) -> bool:
        """
        Remove addon from system.
        
        Args:
            addon_id: Unique identifier for the addon
            
        Returns:
            True if unregistration successful, False otherwise
        """
        try:
            if addon_id in self.registered_addons:
                del self.registered_addons[addon_id]

            if addon_id in self.addon_handlers:
                del self.addon_handlers[addon_id]

            self.logger.info(f"Unregistered addon: {addon_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Error unregistering addon {addon_id}: {str(e)}"
            )
            return False

    def get_available_tools(self) -> list:
        """
        Get all available tools for agent context.
        
        Returns:
            List of all tool specifications from all registered addons
        """
        all_tools = []

        for addon_id, manifest in self.registered_addons.items():
            for tool in manifest.get_tools():
                tool_spec = tool.copy()
                tool_spec['addon_id'] = addon_id
                tool_spec['addon_name'] = manifest.addon_info.get(
                    'name', addon_id
                )
                all_tools.append(tool_spec)

        return all_tools

    def get_addon_manifest(self, addon_id: str):
        """
        Get manifest for specific addon.
        
        Args:
            addon_id: Unique identifier for the addon
            
        Returns:
            AddonManifest object if found, None otherwise
        """
        return self.registered_addons.get(addon_id)

    def get_addon_handlers(self, addon_id: str):
        """
        Get command handlers for specific addon.
        
        Args:
            addon_id: Unique identifier for the addon
            
        Returns:
            Dictionary of handlers if found, None otherwise
        """
        return self.addon_handlers.get(addon_id)

    def get_registered_addons(self) -> dict:
        """
        Get all registered addons.
        
        Returns:
            Dictionary of all registered addons (copy)
        """
        return self.registered_addons.copy()

    def refresh_registry(self) -> int:
        """
        Refresh the registry by rescanning for addons.
        
        Returns:
            Number of addons after refresh
        """
        self.logger.info("Refreshing addon registry...")

        # Clear current registry
        old_count = len(self.registered_addons)
        self.registered_addons.clear()
        self.addon_handlers.clear()

        # Rescan
        discovered = self.scan_addons()
        new_count = len(self.registered_addons)

        self.logger.info(
            f"Registry refreshed: {old_count} -> {new_count} addons"
        )
        return new_count
