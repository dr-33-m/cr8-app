#!/usr/bin/env python3
import asyncio
import logging

from src import WebSocketServer


def setup_logging():
    """Configure logging for the application."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('websocket_server.log'),
            logging.StreamHandler()
        ]
    )


def main():
    """Entry point for the WebSocket server."""
    # Setup logging
    setup_logging()

    # Create and start the server
    server = WebSocketServer()

    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        print("Server stopped by user.")
    except Exception as e:
        logging.error(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
