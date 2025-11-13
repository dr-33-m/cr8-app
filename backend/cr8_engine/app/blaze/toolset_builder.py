"""
Toolset Builder - Creates dynamic AI toolsets from addon registry data
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic_ai.toolsets import FunctionToolset

logger = logging.getLogger(__name__)


class ToolsetBuilder:
    """Builds dynamic toolsets for B.L.A.Z.E agent from addon registry data"""

    def __init__(self, agent_instance):
        """Initialize toolset builder with agent reference"""
        self.agent_instance = agent_instance

    def build_toolset_from_registry(self, registry_data: Dict[str, Any]) -> Optional[FunctionToolset]:
        """Build dynamic toolset from registry data"""
        try:
            available_tools = registry_data.get('available_tools', [])
            if not available_tools:
                logger.debug("No tools in registry data")
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
                        logger.warning(
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

                    logger.debug(
                        f"Added dynamic tool to toolset: {tool_name} with {len(tool_params)} parameters")

            logger.info(
                f"Built dynamic toolset with {len(toolset.tools)} tools from registry")

            return toolset

        except Exception as e:
            logger.error(f"Error building dynamic toolset from registry: {str(e)}")
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
    
    return await self.agent_instance.execute_addon_command_direct('{addon_id}', '{tool_name}', filtered_params)
'''

        # Create namespace and execute function definition
        namespace = {'self': self}

        exec(function_code, namespace)
        dynamic_function = namespace[tool_name]

        logger.debug(f"Created function {tool_name} with signature: {signature_str}")

        return dynamic_function
