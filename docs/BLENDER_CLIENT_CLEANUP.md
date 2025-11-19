# Blender Client 5-Minute Cleanup Implementation

## Overview

When the cr8_engine server becomes unavailable, the Blender client (cr8_router addon) will automatically save and close after 5 minutes of failed connection attempts. This ensures clean resource management and allows the browser client to relaunch Blender when the server returns online.

## Architecture

### Connection Flow

```
Blender connects to cr8_engine server
    ↓
Server available → Normal operation
    ↓
Server goes down → Socket.IO auto-retry (5 attempts)
    ↓
All retries exhausted → on_disconnect event fires
    ↓
Start 5-minute cleanup timer
    ↓
After 5 minutes → Save file + Quit Blender
    ↓
Browser client detects server is back online
    ↓
Browser relaunches Blender with saved file
```

## Implementation Details

### 1. WebSocketHandler Timer Management

**File:** `backend/cr8_router/ws/websocket_handler.py`

#### Attributes

- `server_cleanup_timer`: Reference to the registered Blender timer function

#### Methods

**`start_server_cleanup_timer()`**

- Called when Socket.IO disconnects after exhausting retry attempts
- Logs warning message about impending cleanup
- Registers a Blender timer to execute after 300 seconds (5 minutes)
- Uses `bpy.app.timers.register()` for main thread execution

**`perform_server_cleanup()`**

- Executed after 5-minute timer expires
- Saves the current .blend file using `bpy.ops.wm.save_mainfile()`
- Quits Blender gracefully using `bpy.ops.wm.quit_blender()`
- Includes error handling to ensure Blender closes even if save fails

### 2. Event Handler Integration

**File:** `backend/cr8_router/ws/handlers/event_handlers.py`

**`on_disconnect` handler**

- Triggered when Socket.IO connection is lost
- Clears processing state
- Calls `handler.start_server_cleanup_timer()` via main thread execution
- Ensures timer is started safely in Blender's main thread

## Key Design Decisions

### Why 5 Minutes?

- **Socket.IO Retry Attempts**: Configured for 5 attempts with exponential backoff (2-10 seconds)
- **Total Retry Time**: ~30-40 seconds of automatic retry attempts
- **Grace Period**: 5 minutes provides ample time for server to recover
- **Resource Management**: Prevents indefinite resource consumption from idle Blender instances

### Why Save Before Quit?

- **Data Preservation**: Ensures user work is not lost
- **Browser Relaunch**: When browser client relaunches Blender, the saved file is available
- **Clean State**: File is saved to disk, ready for next session

### Why Blender Timers?

- **Thread Safety**: `bpy.app.timers` executes in Blender's main thread
- **Consistency**: Uses same pattern as existing main thread execution
- **Reliability**: Blender's timer system is designed for this use case

## Logging

The implementation includes comprehensive logging at each stage:

```
[WARNING] Server unreachable after 5 connection attempts.
          Blender will save and close in 5 minutes if server does not reconnect.

[INFO] 5-minute server cleanup timer started

[INFO] Performing server cleanup: saving file and closing Blender
[INFO] Saving Blender file: /path/to/file.blend
[INFO] Closing Blender instance
```

## Error Handling

The cleanup process includes robust error handling:

1. **Save Failure**: If file save fails, logs error but continues to quit
2. **Quit Failure**: If quit fails, logs error (Blender may still close)
3. **Timer Unregister**: Safely handles cases where timer cannot be unregistered

## Integration with Browser Client

The Blender cleanup works in tandem with the browser client cleanup:

| Component      | Timeout    | Action                                            |
| -------------- | ---------- | ------------------------------------------------- |
| Browser Client | 5 minutes  | Clears stores, shows "server unavailable" message |
| Blender Client | 5 minutes  | Saves file, quits Blender                         |
| Browser Client | Reconnects | Detects server is back, relaunches Blender        |

## Testing Scenarios

### Scenario 1: Normal Server Downtime

1. Start Blender with cr8_router addon connected
2. Stop cr8_engine server
3. Observe Socket.IO retry attempts in logs
4. After retries exhausted, see cleanup timer start message
5. After 5 minutes, Blender saves and closes
6. Restart cr8_engine server
7. Browser client reconnects and relaunches Blender

### Scenario 2: Server Recovery Before Timeout

1. Start Blender with cr8_router addon connected
2. Stop cr8_engine server
3. Observe cleanup timer start
4. Restart cr8_engine server within 5 minutes
5. Socket.IO reconnects (if auto-retry succeeds)
6. Blender continues running normally
7. No cleanup occurs

### Scenario 3: File Preservation

1. Create/modify a Blender file
2. Trigger server disconnect
3. Wait for 5-minute cleanup
4. Observe file is saved before Blender closes
5. Restart server and browser client
6. Verify saved file is available for relaunch

## Configuration

### Timeout Duration

To modify the 5-minute timeout, edit `websocket_handler.py`:

```python
# Change this value (in seconds)
self.server_cleanup_timer = bpy.app.timers.register(
    cleanup_timer,
    first_interval=300.0  # 300 seconds = 5 minutes
)
```

### Socket.IO Retry Attempts

To modify retry behavior, edit `websocket_handler.py`:

```python
self.sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=5,      # Number of retry attempts
    reconnection_delay=2,          # Initial delay in seconds
    reconnection_delay_max=10      # Maximum delay in seconds
)
```

## Future Enhancements

1. **Configurable Timeout**: Make 5-minute timeout configurable via environment variable
2. **Notification System**: Send notification to browser before cleanup
3. **Graceful Shutdown**: Allow user to cancel cleanup if needed
4. **Metrics**: Track cleanup events for monitoring/debugging
5. **Recovery Attempts**: Implement custom reconnection logic before cleanup

## Related Documentation

- [Browser Client Cleanup](./BROWSER_CLIENT_CLEANUP.md)
- [Blender AI Router Architecture](./BLENDER_MULTI_ADDON_ARCHITECTURE.md)
- [Backend Architecture](./BLAZE_ARCHITECTURE.md)
