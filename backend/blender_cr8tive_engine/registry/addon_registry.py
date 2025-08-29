"""
AI Addon Registry - Manages discovery and validation of AI-capable addons
"""

import os
import json
import logging
import bpy
from pathlib import Path

logger = logging.getLogger(__name__)


class AddonManifest:
    """Represents a parsed and validated addon manifest"""

    def __init__(self, addon_id: str, manifest_data: dict, addon_path: Path):
        self.addon_id = addon_id
        self.manifest_data = manifest_data
        self.addon_path = addon_path

        # Parse core info
        self.addon_info = manifest_data.get('addon_info', {})
        self.ai_integration = manifest_data.get('ai_integration', {})

        # Validation
        self.is_valid = self._validate()

    def _validate(self) -> bool:
        """Validate manifest structure and requirements"""
        try:
            # Check required fields
            required_addon_fields = ['id', 'name',
                                     'version', 'author', 'category']
            for field in required_addon_fields:
                if field not in self.addon_info:
                    logger.error(f"Missing required addon_info field: {field}")
                    return False

            # Check AI integration
            if 'agent_description' not in self.ai_integration:
                logger.error(
                    "Missing required ai_integration.agent_description")
                return False

            if 'tools' not in self.ai_integration:
                logger.warning(f"No tools defined for addon {self.addon_id}")
                self.ai_integration['tools'] = []

            # Validate tools
            for tool in self.ai_integration.get('tools', []):
                if not self._validate_tool(tool):
                    return False

            # Check Blender version compatibility
            requirements = self.ai_integration.get('requirements', {})
            min_version = requirements.get('blender_version_min')
            if min_version:
                current_version = bpy.app.version_string
                # Basic version check (could be enhanced)
                if current_version < min_version:
                    logger.warning(
                        f"Addon {self.addon_id} requires Blender {min_version}, current: {current_version}")

            return True

        except Exception as e:
            logger.error(
                f"Validation error for addon {self.addon_id}: {str(e)}")
            return False

    def _validate_tool(self, tool: dict) -> bool:
        """Validate individual tool definition"""
        required_fields = ['name', 'description', 'usage']
        for field in required_fields:
            if field not in tool:
                logger.error(f"Tool missing required field: {field}")
                return False

        # Validate parameters
        for param in tool.get('parameters', []):
            if not self._validate_parameter(param):
                return False

        return True

    def _validate_parameter(self, param: dict) -> bool:
        """Validate tool parameter definition"""
        required_fields = ['name', 'type', 'description', 'required']
        for field in required_fields:
            if field not in param:
                logger.error(f"Parameter missing required field: {field}")
                return False

        # Validate parameter type
        valid_types = [
            'string', 'integer', 'float', 'boolean',
            'object_name', 'material_name', 'collection_name',
            'enum', 'vector3', 'color', 'file_path'
        ]
        if param['type'] not in valid_types:
            logger.error(f"Invalid parameter type: {param['type']}")
            return False

        return True

    def get_tools(self) -> list:
        """Get list of tools provided by this addon"""
        return self.ai_integration.get('tools', [])

    def get_tool_by_name(self, tool_name: str):
        """Get specific tool by name"""
        for tool in self.get_tools():
            if tool['name'] == tool_name:
                return tool
        return None


class AIAddonRegistry:
    """Registry for managing AI-capable addons"""

    def __init__(self):
        self.registered_addons: dict = {}
        self.addon_handlers: dict = {}
        self.logger = logging.getLogger(__name__)

        # Initialize registry
        self.scan_addons()

    def scan_addons(self) -> list:
        """Discover and load addon manifests from Blender addons directory"""
        self.logger.info("Scanning for AI-capable addons...")

        discovered_addons = []

        # Get Blender's addons directories
        addon_paths = self._get_addon_paths()

        for addon_path in addon_paths:
            if addon_path.exists() and addon_path.is_dir():
                discovered_addons.extend(self._scan_directory(addon_path))

        self.logger.info(
            f"Discovered {len(discovered_addons)} AI-capable addons")
        return discovered_addons

    def _get_addon_paths(self) -> list:
        """Get all possible addon paths in Blender"""
        addon_paths = []

        # User addons directory
        if hasattr(bpy.utils, 'user_script_path'):
            user_scripts = bpy.utils.user_script_path()
            if user_scripts:
                addon_paths.append(Path(user_scripts) / "addons")

        # System addons directories
        for path in bpy.utils.script_paths():
            addon_paths.append(Path(path) / "addons")

        return addon_paths

    def _scan_directory(self, directory: Path) -> list:
        """Scan a directory for AI-capable addons"""
        discovered = []

        for item in directory.iterdir():
            if item.is_dir():
                manifest_path = item / "addon_ai.json"
                if manifest_path.exists():
                    try:
                        manifest = self._load_manifest(item, manifest_path)
                        if manifest and manifest.is_valid:
                            discovered.append(manifest)
                            # Try to register immediately
                            self.register_addon(manifest.addon_id, manifest)
                    except Exception as e:
                        self.logger.error(
                            f"Error loading manifest from {item}: {str(e)}")

        return discovered

    def _load_manifest(self, addon_path: Path, manifest_path: Path):
        """Load and parse an addon manifest file"""
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                manifest_data = json.load(f)

            addon_id = manifest_data.get('addon_info', {}).get('id')
            if not addon_id:
                self.logger.error(
                    f"No addon ID found in manifest at {manifest_path}")
                return None

            return AddonManifest(addon_id, manifest_data, addon_path)

        except json.JSONDecodeError as e:
            self.logger.error(
                f"JSON parsing error in {manifest_path}: {str(e)}")
            return None
        except Exception as e:
            self.logger.error(
                f"Error loading manifest {manifest_path}: {str(e)}")
            return None

    def validate_manifest(self, manifest: dict) -> bool:
        """Validate manifest format and requirements"""
        try:
            temp_manifest = AddonManifest("temp", manifest, Path())
            return temp_manifest.is_valid
        except Exception as e:
            self.logger.error(f"Manifest validation error: {str(e)}")
            return False

    def register_addon(self, addon_id: str, manifest: AddonManifest) -> bool:
        """Register addon in the system"""
        try:
            if not manifest.is_valid:
                self.logger.error(f"Cannot register invalid addon: {addon_id}")
                return False

            # Check for conflicts
            if addon_id in self.registered_addons:
                self.logger.warning(
                    f"Addon {addon_id} already registered, updating...")

            # Store manifest
            self.registered_addons[addon_id] = manifest

            # Try to load command handlers from the addon
            self._load_addon_handlers(addon_id, manifest)

            self.logger.info(f"Successfully registered addon: {addon_id}")
            return True

        except Exception as e:
            self.logger.error(f"Error registering addon {addon_id}: {str(e)}")
            return False

    def _load_addon_handlers(self, addon_id: str, manifest: AddonManifest) -> bool:
        """Load command handlers from the addon's Python module"""
        try:
            # Try to import the addon module
            addon_module_name = manifest.addon_path.name

            # Check if addon is enabled in Blender
            if addon_module_name not in bpy.context.preferences.addons:
                self.logger.warning(
                    f"Addon {addon_id} is not enabled in Blender")
                return False

            # Import the addon module
            import importlib
            addon_module = importlib.import_module(addon_module_name)

            # Look for AI_COMMAND_HANDLERS export
            if hasattr(addon_module, 'AI_COMMAND_HANDLERS'):
                handlers = addon_module.AI_COMMAND_HANDLERS
                if isinstance(handlers, dict):
                    self.addon_handlers[addon_id] = handlers
                    self.logger.info(
                        f"Loaded {len(handlers)} handlers for addon {addon_id}")
                    return True
                else:
                    self.logger.error(
                        f"AI_COMMAND_HANDLERS must be a dict in addon {addon_id}")
            else:
                self.logger.warning(
                    f"No AI_COMMAND_HANDLERS found in addon {addon_id}")

            return False

        except ImportError as e:
            self.logger.error(f"Failed to import addon {addon_id}: {str(e)}")
            return False
        except Exception as e:
            self.logger.error(
                f"Error loading handlers for addon {addon_id}: {str(e)}")
            return False

    def unregister_addon(self, addon_id: str) -> bool:
        """Remove addon from system"""
        try:
            if addon_id in self.registered_addons:
                del self.registered_addons[addon_id]

            if addon_id in self.addon_handlers:
                del self.addon_handlers[addon_id]

            self.logger.info(f"Unregistered addon: {addon_id}")
            return True

        except Exception as e:
            self.logger.error(
                f"Error unregistering addon {addon_id}: {str(e)}")
            return False

    def get_available_tools(self) -> list:
        """Get all available tools for agent context"""
        all_tools = []

        for addon_id, manifest in self.registered_addons.items():
            for tool in manifest.get_tools():
                tool_spec = tool.copy()
                tool_spec['addon_id'] = addon_id
                tool_spec['addon_name'] = manifest.addon_info.get(
                    'name', addon_id)
                all_tools.append(tool_spec)

        return all_tools

    def get_addon_manifest(self, addon_id: str):
        """Get manifest for specific addon"""
        return self.registered_addons.get(addon_id)

    def get_addon_handlers(self, addon_id: str):
        """Get command handlers for specific addon"""
        return self.addon_handlers.get(addon_id)

    def get_registered_addons(self) -> dict:
        """Get all registered addons"""
        return self.registered_addons.copy()

    def refresh_registry(self) -> int:
        """Refresh the registry by rescanning for addons"""
        self.logger.info("Refreshing addon registry...")

        # Clear current registry
        old_count = len(self.registered_addons)
        self.registered_addons.clear()
        self.addon_handlers.clear()

        # Rescan
        discovered = self.scan_addons()
        new_count = len(self.registered_addons)

        self.logger.info(
            f"Registry refreshed: {old_count} -> {new_count} addons")
        return new_count
