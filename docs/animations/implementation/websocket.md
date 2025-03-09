# WebSocket Communication

This document details the WebSocket communication protocol used by the Animation System, covering message formats, command structure, and error handling.

## Overview

The Animation System uses WebSocket communication to enable real-time interaction between the frontend and the backend. This allows for immediate feedback when applying animations to the 3D scene.

The communication flow follows this pattern:

1. Frontend sends animation commands to cr8_engine via WebSocket
2. cr8_engine forwards commands to blender_cr8tive_engine
3. blender_cr8tive_engine executes the commands in Blender
4. Results are sent back through the same path in reverse

## WebSocket Connection

### Connection Establishment

The WebSocket connection is established when the user loads the application. The connection URL includes the username and template information:

```typescript
// frontend/hooks/useWebsocket.ts

const getWebSocketUrl = useCallback(() => {
  if (!userInfo?.username || !template) {
    return null;
  }
  return `${websocketUrl}/${userInfo.username}/browser?blend_file=${template}`;
}, [userInfo?.username, template, websocketUrl]);
```

### Connection Management

The WebSocket connection is managed by the `useWebSocket` hook, which handles connection establishment, reconnection, and message sending:

```typescript
// frontend/hooks/useWebsocket.ts

export const useWebSocket = (onMessage?: (data: any) => void) => {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  // ... other state and refs

  const connect = useCallback(() => {
    const url = getWebSocketUrl();
    if (!url) {
      toast.error("Missing connection details");
      return;
    }

    // ... connection logic

    try {
      setStatus("connecting");
      const ws = new WebSocket(url);
      websocketRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        // ... handle successful connection
      };

      ws.onclose = (event) => {
        // ... handle connection close
      };

      ws.onerror = (error) => {
        // ... handle connection error
      };

      ws.onmessage = (event) => {
        // ... handle incoming messages
      };
    } catch (error) {
      // ... handle connection failure
    }
  }, [getWebSocketUrl, sendMessage, attemptReconnect]);

  // ... other methods

  return {
    status,
    websocket: websocketRef.current,
    isConnected: status === "connected",
    reconnect,
    disconnect,
    sendMessage,
    requestTemplateControls,
  };
};
```

## Message Format

### Command Messages

Commands sent from the frontend to the backend follow a standard format:

```typescript
interface WebSocketMessage {
  command: string; // The command to execute
  empty_name?: string; // The target empty (for animation commands)
  data?: any; // Command-specific data
  message_id?: string; // Unique ID for tracking the command
}
```

### Response Messages

Responses from the backend to the frontend also follow a standard format:

```typescript
interface WebSocketResponse {
  command: string; // The command that was executed
  status: "success" | "error"; // The status of the command
  message?: string; // A message describing the result
  message_id?: string; // The ID of the original command
  data?: any; // Command-specific response data
}
```

## Animation Commands

### Camera Animation Command

```json
{
  "command": "load_camera_animation",
  "empty_name": "Camera",
  "data": {
    "animation_id": "cam_orbit_01",
    "parameters": {
      "duration": 5.0,
      "easing": "ease-in-out"
    }
  },
  "message_id": "anim_1234567890"
}
```

### Light Animation Command

```json
{
  "command": "load_light_animation",
  "empty_name": "Light",
  "data": {
    "animation_id": "light_pulse_01",
    "parameters": {
      "duration": 3.0,
      "intensity": 1.5
    }
  },
  "message_id": "anim_1234567891"
}
```

### Product Animation Command

```json
{
  "command": "load_product_animation",
  "empty_name": "Product",
  "data": {
    "animation_id": "product_rotate_01",
    "parameters": {
      "duration": 4.0,
      "rotation_axis": "z"
    }
  },
  "message_id": "anim_1234567892"
}
```

## Animation Responses

### Success Response

```json
{
  "command": "animation_result",
  "status": "success",
  "message": "Animation applied successfully",
  "message_id": "anim_1234567890",
  "data": {
    "animation_id": "cam_orbit_01",
    "target": "Camera",
    "duration": 5.0
  }
}
```

### Error Response

```json
{
  "command": "animation_result",
  "status": "error",
  "message": "Error applying animation: Target empty not found",
  "message_id": "anim_1234567890"
}
```

## Message Handling

### Frontend Message Handling

The frontend handles WebSocket messages using the `processWebSocketMessage` function:

```typescript
// frontend/lib/handlers/websocketMessageHandler.ts

export function processWebSocketMessage(data: any, handlers: MessageHandlers) {
  const { command } = data;

  switch (command) {
    case "animation_result":
      if (handlers.onAnimationResponse) {
        handlers.onAnimationResponse(data);
      }
      break;
    case "template_controls_result":
      if (handlers.onTemplateControls) {
        handlers.onTemplateControls(data.data);
      }
      break;
    default:
      if (handlers.onCustomMessage) {
        handlers.onCustomMessage(data);
      }
      break;
  }
}
```

### cr8_engine Message Handling

The cr8_engine handles WebSocket messages using the `WebSocketHandler` class:

```python
# backend/cr8_engine/app/realtime_engine/websockets/websocket_handler.py

class WebSocketHandler:
    def __init__(self):
        self.handler_registry = HandlerRegistry()
        self.register_handlers()

    def register_handlers(self):
        # Register animation handlers
        self.handler_registry.register_handler("load_camera_animation", AnimationHandler())
        self.handler_registry.register_handler("load_light_animation", AnimationHandler())
        self.handler_registry.register_handler("load_product_animation", AnimationHandler())
        # ... other handlers

    async def handle_message(self, message: dict, websocket: WebSocket):
        command = message.get("command")
        if not command:
            return {"status": "error", "message": "No command specified"}

        handler = self.handler_registry.get_handler(command)
        if not handler:
            return {"status": "error", "message": f"No handler for command: {command}"}

        return await handler.handle(message, websocket)
```

### blender_cr8tive_engine Message Handling

The blender_cr8tive_engine handles WebSocket messages using a similar approach:

```python
# backend/blender_cr8tive_engine/ws/websocket_handler.py

class WebSocketHandler:
    def __init__(self):
        self.handler_registry = HandlerRegistry()
        self.register_handlers()

    def register_handlers(self):
        # Register animation handlers
        self.handler_registry.register_handler("load_camera_animation", AnimationHandler())
        self.handler_registry.register_handler("load_light_animation", AnimationHandler())
        self.handler_registry.register_handler("load_product_animation", AnimationHandler())
        # ... other handlers

    async def handle_message(self, message: dict):
        command = message.get("command")
        if not command:
            return {"status": "error", "message": "No command specified"}

        handler = self.handler_registry.get_handler(command)
        if not handler:
            return {"status": "error", "message": f"No handler for command: {command}"}

        return await handler.handle(message)
```

## Message Routing

### Frontend to cr8_engine

The frontend sends messages to cr8_engine using the `sendMessage` function from the WebSocket context:

```typescript
// frontend/hooks/useAnimations.ts

const applyAnimation = useCallback(
  (animation: Animation, emptyName: string) => {
    try {
      // Create a unique message ID for tracking
      const messageId = `anim_${Date.now()}_${Math.random()
        .toString(36)
        .substring(2, 9)}`;

      // Convert template_type to command type
      const animationType =
        animation.template_type === "product_animation"
          ? "product"
          : animation.template_type;

      // Determine the command based on animation type
      const command = `load_${animationType}_animation`;

      // Send the animation command via WebSocket
      sendMessage({
        command,
        empty_name: emptyName,
        data: animation.templateData,
        message: messageId,
      });

      toast.success(`Applying ${animationType} animation: ${animation.name}`);
    } catch (error) {
      console.error("Error applying animation:", error);
      toast.error("Failed to apply animation");
    }
  },
  [sendMessage]
);
```

### cr8_engine to blender_cr8tive_engine

The cr8_engine forwards messages to blender_cr8tive_engine using the `forward_to_blender` method:

```python
# backend/cr8_engine/app/realtime_engine/websockets/handlers/animation_handler.py

class AnimationHandler(BaseHandler):
    async def handle(self, message: dict, websocket: WebSocket):
        # ... validation logic

        # Forward the command to the Blender engine
        response = await self.forward_to_blender(message)

        return response

    async def forward_to_blender(self, message: dict):
        # Implementation of forwarding to Blender
        # This would typically involve sending the message to the Blender WebSocket server
        # and waiting for a response
        pass
```

## Error Handling

### Frontend Error Handling

The frontend handles errors by catching exceptions and displaying toast notifications:

```typescript
// frontend/hooks/useAnimations.ts

try {
  // ... animation logic
} catch (error) {
  console.error("Error applying animation:", error);
  toast.error("Failed to apply animation");
}
```

### Backend Error Handling

The backend handles errors by catching exceptions and returning error responses:

```python
# backend/blender_cr8tive_engine/ws/handlers/animation.py

try:
    # Execute the animation in Blender
    if command == "load_camera_animation":
        result = self.apply_camera_animation(empty_name, data)
    elif command == "load_light_animation":
        result = self.apply_light_animation(empty_name, data)
    elif command == "load_product_animation":
        result = self.apply_product_animation(empty_name, data)
    else:
        return {
            "command": "animation_result",
            "status": "error",
            "message": f"Unknown animation command: {command}",
            "message_id": message_id
        }

    return {
        "command": "animation_result",
        "status": "success",
        "message": "Animation applied successfully",
        "message_id": message_id,
        "data": result
    }
except Exception as e:
    return {
        "command": "animation_result",
        "status": "error",
        "message": f"Error applying animation: {str(e)}",
        "message_id": message_id
    }
```

## Connection Status Handling

The frontend displays connection status information to the user:

```tsx
// frontend/components/animations/AnimationPanel.tsx

{
  !isConnected ? (
    <div className="mt-4 p-3 bg-yellow-50 text-yellow-800 rounded-md text-sm">
      WebSocket connection is {status}. Animations cannot be applied until
      connected.
    </div>
  ) : null;
}
```

## Reconnection Strategy

The WebSocket connection includes a reconnection strategy with exponential backoff:

```typescript
// frontend/hooks/useWebsocket.ts

const calculateReconnectDelay = useCallback(() => {
  return Math.min(
    BASE_DELAY * Math.pow(2, reconnectAttemptsRef.current),
    MAX_RECONNECT_DELAY
  );
}, []);

const attemptReconnect = useCallback(() => {
  if (isManuallyDisconnected.current) {
    return false;
  }

  if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
    setStatus("failed");
    toast.error(
      "Maximum reconnection attempts reached. Please refresh the page to try again."
    );
    return false;
  }

  const delay = calculateReconnectDelay();
  toast.info(`Attempting to reconnect in ${delay / 1000} seconds...`);

  // Clear any existing timeout
  if (reconnectTimeoutRef.current) {
    clearTimeout(reconnectTimeoutRef.current);
  }

  reconnectTimeoutRef.current = setTimeout(() => {
    reconnectAttemptsRef.current += 1;
    connect();
  }, delay);

  return true;
}, [calculateReconnectDelay]);
```

## Security Considerations

The WebSocket communication includes several security measures:

1. **Authentication**: WebSocket connections are authenticated using JWT tokens
2. **Validation**: Commands are validated before execution
3. **Error Handling**: Error messages are sanitized to prevent information leakage
4. **Rate Limiting**: Excessive message sending is rate-limited

## Conclusion

The WebSocket communication protocol provides a robust foundation for real-time interaction between the frontend and the backend. It enables the Animation System to provide immediate feedback when applying animations to the 3D scene.
