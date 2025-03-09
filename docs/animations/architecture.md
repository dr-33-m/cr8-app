# Cr8tive Engine Architecture

## Overview

The Cr8tive Engine has undergone significant architectural changes to improve modularity and maintainability. The key components are:

### Backend Structure

- **Core Modules**:
  - `ws/`: WebSocket handlers for real-time communication
  - `core/`: Core utilities and controllers
  - `rendering/`: Preview rendering and video generation
  - `templates/`: Template management and wizard

### Frontend Structure

- **New Systems**:
  - Asset Placer: Manages asset placement and transformations
  - Enhanced WebSocket Context: Improved connection handling
  - Animation System: Unified animation controls

### Communication Flow

1. Browser ↔ WebSocket Server ↔ Blender Instance
2. Real-time updates through WebSocket messages
3. State management via Zustand stores

## Key Changes

- Refactored Blender controller architecture
- New asset placement system with undo/redo support
- Improved template handling and controls
- Enhanced error handling and recovery mechanisms
