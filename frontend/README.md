# Cr8-xyz Frontend

## Overview

The frontend is built with Tanstack Start and provides an intuitive interface for interacting with Blender via WebRTC streaming. This is the first implementation of pixel streaming for Blender, allowing real-time viewport interaction.

## Requirements

- Node.js 18.x (LTS)
- pnpm 8.x
- Modern browser (Chrome, Firefox, Edge latest versions)

## Installation

```bash
# Using nvm (recommended)
nvm install 18
nvm use 18

# Install pnpm globally
npm install -g pnpm

# Install dependencies
pnpm install
```

## Development

```bash
# Start development server
pnpm dev

# Build for production
pnpm build

# Start production server
pnpm start
```

## Key Features

- **WebRTC Streaming**: Real-time Blender viewport streaming
- **Tanstack Router**: Modern client-side routing
- **Zustand State Management**: Lightweight state management
- **Tailwind CSS**: Utility-first styling
- **WebSocket Integration**: Real-time communication with Cr8_engine

## Project Structure

```
frontend/
├── app/               # Application routes
├── components/        # React components
├── hooks/             # Custom hooks
├── lib/               # Utilities and services
├── store/             # Zustand state stores
├── styles/            # Global styles
└── public/            # Static assets
```

## Environment Variables

Create a `.env` file with:

```
VITE_WS_URL=ws://localhost:8000/ws
VITE_API_URL=http://localhost:8000/api
```

## Deployment

The frontend is designed to be deployed as a static site. For production:

```bash
pnpm build
# Output will be in dist/ directory
```

## Troubleshooting

- **Node version issues**: Ensure you're using Node 18.x
- **WebRTC connection**: Check firewall settings for WebRTC ports
- **WebSocket errors**: Verify Cr8_engine is running
