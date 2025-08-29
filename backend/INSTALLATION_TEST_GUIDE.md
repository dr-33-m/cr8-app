# Random Mesh Generator Test Addon - Installation & Testing Guide

This guide walks you through properly installing and testing the Random Mesh Generator addon to validate the complete Blender AI Router pipeline.

## Installation Steps

### 1. Locate Your Blender Addons Directory

Find your Blender addons directory based on your operating system:

**Linux:**

```bash
~/.config/blender/[version]/scripts/addons/
# Example: ~/.config/blender/4.2/scripts/addons/
```

**Windows:**

```
%APPDATA%\Blender Foundation\Blender\[version]\scripts\addons\
# Example: C:\Users\YourName\AppData\Roaming\Blender Foundation\Blender\4.2\scripts\addons\
```

**macOS:**

```bash
~/Library/Application Support/Blender/[version]/scripts/addons/
# Example: ~/Library/Application Support/Blender/4.2/scripts/addons/
```

### 2. Install the Test Addon

Copy the entire `random_mesh_generator` folder to your Blender addons directory:

```bash
# Example for Linux
cp -r backend/test_addons/random_mesh_generator/ ~/.config/blender/4.2/scripts/addons/
```

### 3. Enable the Addon in Blender

1. Open Blender
2. Go to **Edit > Preferences > Add-ons**
3. Search for "Random Mesh Generator"
4. Enable the checkbox next to "Testing: Random Mesh Generator"
5. The addon should now appear in Blender's Add menu

### 4. Verify Blender Integration

Test the addon directly in Blender first:

1. Go to **Add > Mesh > Random Mesh Generator**
2. Try each option:
   - Random Cube
   - Random Sphere
   - Random Cylinder
   - Surprise Me!
3. You should see random meshes being created in the scene

## Testing AI Router Discovery

### 1. Install and Enable the AI Router

The AI Router addon (`backend/blender_cr8tive_engine/`) must also be installed:

```bash
# Copy the AI Router to Blender addons
cp -r backend/blender_cr8tive_engine/ ~/.config/blender/4.2/scripts/addons/blender_ai_router
```

Enable it in Blender preferences:

- Search for "Blender AI Router"
- Enable the addon

### 2. Test Registry Discovery

Create a simple test script in Blender's Text Editor:

```python
import sys
from pathlib import Path

# Access the AI Router registry
import blender_ai_router.registry.addon_registry as registry_module

# Initialize registry
registry = registry_module.AIAddonRegistry()

# Check discovered addons
registered_addons = registry.get_registered_addons()
print(f"Found {len(registered_addons)} AI-capable addons:")

for addon_id, manifest in registered_addons.items():
    addon_info = manifest.addon_info
    tools = manifest.get_tools()
    print(f"- {addon_info.get('name')} (ID: {addon_id})")
    print(f"  Tools: {[tool['name'] for tool in tools]}")

# Test command routing
if 'random_mesh_generator' in registered_addons:
    router = registry_module.AICommandRouter(registry)

    # Test a command
    result = router.route_command(
        command='add_random_cube',
        params={'size': 2.0, 'location': [0, 0, 0]},
        addon_id='random_mesh_generator'
    )
    print(f"Command result: {result}")
else:
    print("Random Mesh Generator not found!")
```

### 3. Expected Results

If everything is working correctly, you should see:

```
Found 1 AI-capable addons:
- Random Mesh Generator (ID: random_mesh_generator)
  Tools: ['add_random_cube', 'add_random_sphere', 'add_random_cylinder', 'add_surprise_mesh']

Command result: {'status': 'success', 'message': 'Added random cube "Cube.001" to scene', 'data': {...}}
```

## Testing Full Pipeline Integration

### 1. Start the Cr8 System

With both addons installed and enabled in Blender:

```bash
# Start the FastAPI server (cr8_engine)
cd backend/cr8_engine
python main.py

# Start Blender with the AI Router addon enabled
# The router will connect to the FastAPI WebSocket
```

### 2. Verify B.L.A.Z.E Capabilities

Check that B.L.A.Z.E now has the new mesh generation tools:

- The DynamicMCPServer should detect the new addon
- B.L.A.Z.E's system prompt should include Random Mesh Generator capabilities
- Users should be able to request mesh creation through the chat interface

### 3. Test Commands Through B.L.A.Z.E

Try asking B.L.A.Z.E:

- "Add a random cube to the scene"
- "Create a sphere with some randomness"
- "Surprise me with a random mesh"

## Marketplace Validation

This test validates the complete marketplace workflow:

1. **✅ Addon Installation**: User copies addon to Blender directory
2. **✅ Blender Registration**: User enables addon in preferences
3. **✅ AI Router Discovery**: Router scans and finds addon manifest
4. **✅ Dynamic Registration**: Router registers addon tools
5. **✅ MCP Integration**: FastAPI receives new capabilities
6. **✅ B.L.A.Z.E Enhancement**: AI agent gains new powers instantly
7. **✅ Command Execution**: Users can use new capabilities immediately

## Troubleshooting

### Addon Not Found

- Verify the addon is copied to the correct directory
- Ensure the addon is enabled in Blender preferences
- Check Blender's console for any import errors

### Registry Issues

- Make sure the AI Router addon is installed and enabled
- Check that both `addon_ai.json` files are valid JSON
- Look for error messages in Blender's console

### Command Failures

- Verify the addon's Python functions work directly in Blender
- Check parameter types and validation
- Ensure Blender has an active scene and proper context

## Next Steps

After successful testing:

1. Create additional test addons for different categories
2. Test with multiple addons installed simultaneously
3. Validate the complete user experience from addon installation to AI interaction
4. Document the addon development process for marketplace creators

This testing validates that the architecture is ready for a real addon marketplace where users can install new capabilities and immediately see them available in B.L.A.Z.E.
