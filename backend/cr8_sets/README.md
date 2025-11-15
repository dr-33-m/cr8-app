# Multi-Registry Asset Manager

AI-capable multi-registry asset addon with direct API access for fast asset search across Polyhaven, BlenderKit, and more.

## Features

- **Multi-Registry Support**: Unified interface for multiple asset registries
- **Polyhaven Integration**: Free high-quality PBR assets (HDRIs, textures, models)
- **AI-Powered Selection**: Intelligent asset scoring and selection
- **Natural Language Search**: Search using plain English descriptions
- **Direct API Calls**: Fast asset access without delays
- **Automatic Scene Integration**: Assets are imported and positioned automatically
- **B.L.A.Z.E Compatible**: Full integration with AI orchestration systems

## Supported Registries

### Polyhaven (Active)

- **Status**: ✅ Fully Operational
- **Assets**: HDRIs, PBR Textures, 3D Models
- **Authentication**: None required (free API)
- **Quality**: Professional, curated, CC0 licensed
- **Resolution**: Up to 8K for textures/HDRIs

### BlenderKit (Coming Soon)

- **Status**: 🔧 Under Development
- **Assets**: Models, Materials, Brushes, HDRs, Scenes
- **Authentication**: API key required
- **Quality**: Community-driven with validation system

## AI Integration

This addon is designed for AI-only interaction through B.L.A.Z.E/CR8 systems. It exports the following AI command handlers:

### Polyhaven Functions

- `search_polyhaven_assets()` - Natural language asset search
- `download_polyhaven_asset()` - Download and import specific assets
- `find_and_add_polyhaven_asset()` - Complete workflow in one step
- `get_polyhaven_categories()` - Discover available asset categories
- `apply_polyhaven_texture_to_object()` - Apply textures to objects

### Generic Functions

- `search_assets()` - Multi-registry search
- `download_asset()` - Multi-registry download

## Usage Examples

### Search for Assets

```python
# Search for modern furniture models
search_polyhaven_assets("modern chair", "model", 10)

# Find brick textures
search_polyhaven_assets("brick wall", "texture", 5, "outdoor,brick")

# Get dramatic HDR environments
search_polyhaven_assets("sunset dramatic", "hdri", 3)
```

### Download and Import Assets

```python
# Download specific asset by ID
download_polyhaven_asset("wooden_table_01", True, 2.0, 0.0, 0.0, "2k")

# Complete workflow - search, select, download, import
find_and_add_polyhaven_asset("comfortable office chair", "model", 1.0, 1.0, 0.0, "4k")
```

### Apply Textures

```python
# Apply downloaded texture to object
apply_polyhaven_texture_to_object("Cube", "brick_wall_01")
```

## Architecture

The addon uses a registry pattern for extensibility:

- `registry_base.py` - Abstract base classes and interfaces
- `polyhaven_registry.py` - Polyhaven implementation with proven blender-mcp code
- `multi_registry_handlers.py` - AI handlers for B.L.A.Z.E integration
- `__init__.py` - Addon registration and AI command exports
- `addon_ai.json` - AI integration configuration

## Installation

1. Copy addon files to Blender addons directory
2. Enable "Multi-Registry Asset Manager" in Blender preferences
3. No additional configuration needed for Polyhaven (free API)

## AI Capabilities

The addon provides natural language interface for:

- Asset discovery and search
- Intelligent asset selection based on quality and relevance
- Automatic scene integration with proper positioning
- PBR material setup with complete node connections
- HDR environment configuration
- Cross-registry asset management

## Technical Details

### Asset Types Supported

- **Models**: GLTF, FBX, OBJ, Blend files
- **Textures**: JPG, PNG with PBR map support (diffuse, normal, roughness, metallic, etc.)
- **HDRIs**: HDR, EXR formats with automatic world setup

### Quality Features

- Automatic color space management
- Proper PBR material node connections
- Dependency resolution for complex assets
- Temporary file cleanup
- Error handling and recovery

### Registry System

- Extensible architecture for adding new registries
- Standardized asset metadata format
- Registry-agnostic AI handlers
- Unified search and download interface

## Development Status

- ✅ Polyhaven registry fully implemented
- ✅ AI integration with B.L.A.Z.E complete
- ✅ Natural language search working
- ✅ Asset import and scene integration operational
- 🔧 BlenderKit registry (pending - original system needs fixing)
- 🔧 Cross-registry search capabilities
- 🔧 Additional registry support (Sketchfab, etc.)

## License

This addon integrates with:

- Polyhaven: CC0 licensed assets (public domain)
- BlenderKit: Various licenses per asset

The addon code itself follows the project license terms.
