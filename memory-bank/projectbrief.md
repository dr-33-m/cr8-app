# Project Brief: Cr8-xyz CGI Content Creation Platform

## Overview

Cr8-xyz is a CGI content creation platform powered by Blender as the creative engine. Our mission is to democratize 3D content creation by putting the power of Blender in everyone's hands through natural language interfaces and AI automation. The system enables AI-assisted 3D content creation with real-time viewport streaming and collaborative workflow automation through a distributed three-tier architecture.

## Core Components

- **Frontend**: Tanstack-based interface with WebRTC streaming for real-time Blender viewport interaction
- **Cr8 Engine**: FastAPI WebSocket server acting as central communication hub between frontend, Blender addon, and AI agents
- **Blender Creative Engine**: Headless Blender addon for remote control, WebRTC streaming, and AI-assisted 3D content creation
- **Template System**: Pre-built templates for cameras, lights, and products with wizard-based scene setup
- **WebSocket Communication**: Dual endpoint architecture with pattern-based message routing and session management

## Key Features

- **AI-Assisted Creation**: Natural language interfaces and AI automation for 3D content creation
- **Real-time Viewport Streaming**: WebRTC-based Blender viewport streaming for instant feedback
- **Intelligent Asset Management**: Append/remove assets with transform controls and information retrieval
- **Template Wizard System**: Pre-built templates with parameter management and preset loading
- **Dual WebSocket Architecture**: Pattern-based message routing with exponential backoff session management
- **MCP Server Integration**: Tool integration for AI agents with context management

## Project Goals

1. **Democratize 3D Creation**: Make Blender's powerful 3D capabilities accessible through intuitive natural language interfaces
2. **Enable AI Collaboration**: Integrate AI automation to assist creators in their 3D content creation workflows
3. **Provide Real-time Interaction**: Deliver instant feedback through WebRTC viewport streaming and collaborative features
4. **Maintain Scalable Architecture**: Support extensible template systems and modular component integration
5. **Foster Community Creation**: Enable seamless sharing and collaboration through distributed architecture

## Scope

This project encompasses the full-stack development of a CGI content creation platform that integrates Blender's powerful 3D capabilities with AI automation, natural language interfaces, and real-time WebRTC viewport streaming. The platform enables democratized access to professional 3D content creation through a distributed three-tier architecture supporting collaborative workflows and intelligent asset management.
