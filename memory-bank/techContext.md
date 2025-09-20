# Technical Context: Cr8-xyz Technology Stack

## Core Technologies

### Frontend

- **Framework**: React with TypeScript (TanStack-based)
- **Build Tool**: Vite with Vinxi for SSR/SSG
- **Styling**: Tailwind CSS with custom component library
- **Routing**: TanStack Router with file-based routing
- **State Management**: Zustand stores and React contexts
- **UI Components**: Radix UI primitives with custom components
- **Real-time**: WebSocket integration with exponential backoff
- **Streaming**: WebRTC viewport streaming with gstwebrtc-api
- **Package Manager**: pnpm
- **Form Handling**: React Hook Form with Zod validation

### Backend (Cr8 Engine)

- **Language**: Python 3.x
- **Framework**: FastAPI with uvicorn
- **WebSockets**: Starlette WebSocket support with session management
- **AI Integration**: Pydantic AI with OpenRouter provider
- **Dependencies**: requirements.txt managed with venv isolation
- **API Structure**: RESTful endpoints with /api/v1/ hierarchy
- **Real-time Engine**: Custom WebSocket session manager and handlers
- **Service Layer**: Blender service for instance management

### Blender Integration

- **Platform**: Blender 3D (Python API) with addon system
- **Addon System**: Multi-addon architecture with AI Router
- **Registry Pattern**: Manifest-based discovery (addon_ai.json)
- **WebSocket Communication**: Real-time message handling with threading
- **Command Routing**: Dynamic parameter validation and type checking
- **Response Management**: Standardized response format with message IDs
- **AI Integration**: Natural language command processing

## Development Environment

### Version Control

- **Git**: Distributed version control
- **Remote**: code.streetcrisis.online
- **Branch Strategy**: Feature-based development
- **Commit Hash**: 61d3d7abcaee0e4e94b4c03debf75cfbd591247a

### Configuration

- **Rules Engine**: .clinerules configuration system
- **Memory Bank**: Structured documentation approach
- **Security**: Sensitive file protection (.env, manifests)
- **Environment**: Environment variable configuration with dotenv

### Documentation

- **Architecture**: BLAZE_ARCHITECTURE.md and BLENDER_MULTI_ADDON_ARCHITECTURE.md
- **API**: Inline documentation and endpoint definitions
- **Component**: README files throughout structure
- **Memory Bank**: Structured project documentation system

## Communication Patterns

### WebSocket Protocol

- **Message Format**: JSON-based structured messages with message IDs
- **Routing**: Dual endpoint architecture (browser/blender) with session correlation
- **Session Management**: Exponential backoff reconnection with browser refresh detection
- **Error Handling**: Comprehensive error reporting with retry mechanisms
- **Tracking**: Session-based message correlation and operation logging

### API Endpoints

- **Structure**: /api/v1/ endpoint hierarchy
- **Services**: Blend file management and scanning operations
- **Real-time**: WebSocket upgrade support with dual client types
- **Security**: Session-based authentication and authorization patterns

## Integration Points

### AI Agent Integration

- **B.L.A.Z.E Agent**: Pydantic AI agent with dynamic toolset generation
- **OpenRouter**: LLM provider integration for natural language processing
- **Dynamic Capabilities**: Runtime tool discovery from addon manifests
- **Context Management**: Real-time scene state and addon capability tracking

### Template System

- **Operators**: Camera, light, and product template management
- **Properties**: Custom property definitions with validation
- **Panels**: UI panel integration with Blender sidebar
- **Utilities**: Animation and path management utilities

### Addon Registry System

- **Manifest Format**: Standardized addon_ai.json with ai_integration structure
- **Discovery**: Automatic scanning of Blender addon directories
- **Validation**: Type-safe parameter validation and manifest checking
- **Registration**: Dynamic addon registration with capability broadcasting

## Development Practices

### Code Organization

- **Modular Structure**: Clear separation by component type and responsibility
- **Type Safety**: TypeScript interfaces and Python type hints
- **Component Reusability**: UI component library patterns with shadcn/ui
- **Service Layer**: Business logic separation with dedicated service modules

### Testing and Validation

- **Addon Validation**: Manifest validation utilities and format checking
- **Integration Testing**: Cross-component verification with session management
- **Real-time Testing**: WebSocket message flow and reconnection testing
- **AI Validation**: Parameter validation against manifest specifications

### Security Considerations

- **Credential Protection**: Environment variable management and secure storage
- **Parameter Validation**: Type-safe parameter checking and manifest validation
- **File Access Control**: Protected file path management and validation
- **Network Security**: Secure WebSocket communication with session isolation
