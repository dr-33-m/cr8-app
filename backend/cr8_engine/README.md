# WebSocket Server for Blender and Cr8-xyz Integration

## Overview

This WebSocket server facilitates communication between Cr8-xyz Blender addon and Cr8-xyz platform, enabling real-time interaction and frame broadcasting.

## Features

- Robust WebSocket connection management
- Command routing for different client actions
- Frame broadcasting
- Comprehensive logging
- Error handling

## Setup

1. Clone the repository
2. Create a virtual environment
3. Install dependencies:

```bash
pip install -r requirements.txt
```

## Running the Server

```bash
python main.py
```

## Configuration

- Modify host/port in `main.py`
- Adjust logging in `main.py`

## Client Connections

- Blender client connects to '/blender'
- Browser client connects to '/browser'
