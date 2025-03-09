# Cr8 App Documentation

This documentation provides comprehensive information about the Cr8 App, its architecture, components, and usage.

## Table of Contents

- [Animations System](./animations/overview.md)
  - [Architecture](./animations/architecture.md)
  - Implementation Details
    - [Backend Implementation](./animations/implementation/backend.md)
    - [Frontend Implementation](./animations/implementation/frontend.md)
    - [WebSocket Communication](./animations/implementation/websocket.md)
  - [Usage Guide](./animations/usage.md)

## Project Overview

Cr8 is a creative platform that integrates with Blender to provide a web-based interface for manipulating 3D scenes. The application consists of several key components:

1. **Frontend**: A React-based web application that provides the user interface
2. **cr8_engine**: A middleware service that handles API requests and WebSocket communication
3. **blender_cr8tive_engine**: A Blender addon that interfaces with Blender to manipulate 3D scenes

## Key Features

- Real-time scene manipulation via WebSocket communication
- Template-based scene creation and customization
- Animation controls for camera, lighting, and product animations
- Asset management and placement
- Scene configuration and rendering

## Getting Started

Refer to the specific documentation sections for detailed information about each component and feature.
