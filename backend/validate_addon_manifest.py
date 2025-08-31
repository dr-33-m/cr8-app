#!/usr/bin/env python3
"""
Validate addon manifest for the Random Mesh Generator test addon.
This script checks the manifest format without requiring Blender.
"""

import json
import sys
import argparse
from pathlib import Path


def validate_manifest(manifest_path):
    """Validate addon manifest structure"""
    print(f"Validating: {manifest_path}")

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        print("✅ Valid JSON format")

        # Check required sections
        required_sections = ['addon_info', 'ai_integration']
        for section in required_sections:
            if section not in manifest:
                print(f"❌ Missing required section: {section}")
                return False
            print(f"✅ Section found: {section}")

        # Validate addon_info
        addon_info = manifest['addon_info']
        required_fields = ['id', 'name', 'version',
                           'author', 'category', 'description']

        for field in required_fields:
            if field not in addon_info:
                print(f"❌ Missing addon_info.{field}")
                return False
            print(f"✅ addon_info.{field}: {addon_info[field]}")

        # Validate ai_integration
        ai_integration = manifest['ai_integration']

        if 'agent_description' not in ai_integration:
            print("❌ Missing ai_integration.agent_description")
            return False
        print("✅ agent_description found")

        if 'tools' not in ai_integration:
            print("❌ Missing ai_integration.tools")
            return False

        tools = ai_integration['tools']
        print(f"✅ Found {len(tools)} tools")

        # Validate each tool
        for i, tool in enumerate(tools):
            tool_name = tool.get('name', f'tool_{i}')
            print(f"\n  Validating tool: {tool_name}")

            required_tool_fields = [
                'name', 'description', 'usage', 'parameters']
            for field in required_tool_fields:
                if field not in tool:
                    print(f"    ❌ Missing {field}")
                    return False
                print(f"    ✅ {field}")

            # Validate parameters
            params = tool['parameters']
            print(f"    ✅ {len(params)} parameters")

            for j, param in enumerate(params):
                param_name = param.get('name', f'param_{j}')
                required_param_fields = [
                    'name', 'type', 'description', 'required']

                missing_fields = [
                    field for field in required_param_fields if field not in param]
                if missing_fields:
                    print(
                        f"      ❌ Parameter {param_name} missing: {missing_fields}")
                    return False

                # Validate parameter type
                param_type = param['type']
                valid_types = [
                    'string', 'integer', 'float', 'boolean',
                    'object_name', 'material_name', 'collection_name',
                    'enum', 'vector3', 'color', 'file_path'
                ]

                if param_type not in valid_types:
                    print(f"      ❌ Invalid parameter type: {param_type}")
                    return False

                print(f"      ✅ {param_name} ({param_type})")

        print(f"\n🎉 Manifest validation successful!")
        print(f"📦 Addon: {addon_info['name']} v{addon_info['version']}")
        print(f"🔧 Tools: {len(tools)}")
        print(f"📝 Ready for Blender installation!")

        return True

    except json.JSONDecodeError as e:
        print(f"❌ JSON parsing error: {e}")
        return False
    except FileNotFoundError:
        print(f"❌ Manifest file not found: {manifest_path}")
        return False
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate CR8 addon manifest")
    parser.add_argument("manifest_path", 
                       help="Path to addon_ai.json file to validate")
    parser.add_argument("--test-default", action="store_true",
                       help="Test the default random_mesh_generator addon")
    
    args = parser.parse_args()
    
    print("=== CR8 Addon Manifest Validation ===\n")

    if args.test_default:
        # Test the default addon
        manifest_path = Path(__file__).parent / "test_addons" / \
            "random_mesh_generator" / "addon_ai.json"
        print("Testing default addon...")
    else:
        # Use provided path
        manifest_path = Path(args.manifest_path)

    if validate_manifest(manifest_path):
        print("\n✅ Addon manifest is valid!")
        print("\nNext steps:")
        print("1. Copy the addon to your Blender addons directory")
        print("2. Enable it in Blender preferences")
        print("3. Install and enable the AI Router addon")
        print("4. Test the complete pipeline!")
    else:
        print("\n❌ Addon manifest has validation issues.")
        sys.exit(1)
