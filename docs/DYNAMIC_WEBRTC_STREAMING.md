# Dynamic WebRTC Streaming Feature

## Overview

This document describes the implementation of dynamic, per-user WebRTC viewport streaming in the cr8-app Blender integration. This feature enables multiple concurrent users to each have their own Blender instance with unique producer IDs, allowing the browser client to receive real-time viewport streams.

## Architecture

### System Components

```
┌─────────────────┐
│  Browser Client │
│  (React/TS)     │
└────────┬────────┘
         │ WebSocket
         │ (username)
         ▼
┌─────────────────┐
│  Backend        │
│  (FastAPI)      │
└────────┬────────┘
         │ Subprocess
         │ (CR8_USERNAME env)
         ▼
┌─────────────────┐      WebRTC      ┌──────────────┐
│  Blender        │◄─────────────────►│  Signaller   │
│  (Python API)   │                   │  Server      │
└─────────────────┘                   └──────────────┘
         │                                     ▲
         │ WebRTC Stream                       │
         │ (producer_id: blender-{username})   │
         └─────────────────────────────────────┘
```

### Producer ID Format

Each Blender instance uses a unique producer ID based on the username:

```
blender-{username}
```

Example: User "dreem" → Producer ID: "blender-dreem"

## Implementation Details

### 1. Blender C/C++ Layer

#### Files Modified

**`blender/source/blender/python/intern/bpy_app_streaming.cc`**

- Added Python API for WebRTC streaming control
- Implements `bpy.app.streaming` module with methods:
  - `configure(producer_id, signaller_uri, width, height, fps)` - Configure streaming parameters
  - `start()` - Start streaming with configured parameters
  - `stop()` - Stop streaming
  - `is_active()` - Check if streaming is active
  - `get_status()` - Get current status

**Key Implementation Details:**

```cpp
// File-scoped static variables for configuration storage
static char stored_producer_id[256] = {0};
static int stored_width = 1920;
static int stored_height = 1080;
static int stored_fps = 30;
```

**Critical Fix:** Static variables must be at file scope (not function scope) to ensure `configure()` and `start()` share the same storage.

**`blender/source/blender/python/intern/CMakeLists.txt`**

- Added `WITH_STREAMING` preprocessor definition:

```cmake
if(WITH_STREAMING)
  add_definitions(-DWITH_STREAMING)
endif()
```

**Why This Was Needed:** Without this definition, the Python module compiled the `#else` branch that returns "Blender compiled without streaming support", even though the C-level streaming code was compiled correctly.

**`blender/source/blender/python/intern/bpy_app_streaming.cc` (includes)**

- Added `#include "BLI_string.h"` for `BLI_strncpy` function

### 2. Backend Python Layer

#### Files Modified

**`backend/cr8_engine/app/services/blender_service.py`**

- Added `CR8_SIGNALLER_URI` environment variable to Blender subprocess
- Passes signaller server location to each Blender instance

```python
env["CR8_SIGNALLER_URI"] = os.getenv("SIGNALLER_URI", "ws://127.0.0.1:8443")
```

**`backend/cr8_router/ws/handlers/event_handlers.py`**

- Added streaming start logic in `on_connect` handler
- Added streaming stop logic in `on_disconnect` handler

**Streaming Start Implementation:**

```python
def start_streaming():
    """Start WebRTC viewport streaming with dynamic producer ID"""
    try:
        import bpy
        import os

        username = os.environ.get("CR8_USERNAME")
        signaller_uri = os.environ.get("CR8_SIGNALLER_URI", "ws://127.0.0.1:8443")

        if not username:
            logger.error("CR8_USERNAME not set, cannot start streaming")
            return

        producer_id = f"blender-{username}"

        logger.info(f"Starting WebRTC streaming with producer_id: {producer_id}")

        bpy.app.streaming.configure(
            producer_id=producer_id,
            signaller_uri=signaller_uri,
            width=1920,
            height=1080,
            fps=30
        )

        bpy.app.streaming.start()

        logger.info(f"WebRTC streaming started successfully for {username}")
    except Exception as e:
        logger.error(f"Failed to start WebRTC streaming: {e}")
```

### 3. Frontend React/TypeScript Layer

#### Files Modified

**`frontend/app/hooks/useWebRTCStream.ts`**

- Refactored to accept `producerId: string | null` parameter
- Removed hardcoded `VITE_WEBRTC_PRODUCER_ID` environment variable
- Updated to use dynamic producer ID in connection and peer listeners

**Function Signature:**

```typescript
export function useWebRTCStream(producerId: string | null);
```

**Producer Matching:**

```typescript
p.meta.name === producerId;
```

**`frontend/app/routes/workspace/index.tsx`**

- Updated to construct producer ID from username
- Passes dynamic producer ID to `useWebRTCStream` hook

```typescript
const username = useUserStore((state) => state.username);
const producerId = username ? `blender-${username}` : null;
const { videoRef, isConnected } = useWebRTCStream(producerId);
```

## Data Flow

### Streaming Initialization

1. **User Login**

   - User enters username in frontend
   - Username stored in `useUserStore`

2. **Blender Instance Launch**

   - Backend spawns Blender subprocess
   - Sets `CR8_USERNAME` environment variable
   - Sets `CR8_SIGNALLER_URI` environment variable

3. **WebSocket Connection**

   - Blender connects to backend via WebSocket
   - `on_connect` handler triggered

4. **Streaming Start**

   - Handler reads `CR8_USERNAME` from environment
   - Constructs producer ID: `blender-{username}`
   - Calls `bpy.app.streaming.configure()` with producer ID
   - Calls `bpy.app.streaming.start()`
   - Blender begins streaming to signaller server

5. **Browser Connection**
   - Frontend constructs same producer ID: `blender-{username}`
   - Passes to `useWebRTCStream(producerId)`
   - Hook connects to signaller server
   - Listens for producer with matching name
   - Receives and displays stream

### Streaming Cleanup

1. **WebSocket Disconnect**
   - `on_disconnect` handler triggered
   - Calls `bpy.app.streaming.stop()`
   - Cleans up streaming resources

## Configuration

### Environment Variables

**Backend (`backend/cr8_engine/.env`):**

```env
SIGNALLER_URI=ws://127.0.0.1:8443
```

**Frontend (`frontend/.env`):**

```env
VITE_WEBRTC_SIGNALLER_URL=ws://localhost:8443
```

### Streaming Parameters

Default configuration in `event_handlers.py`:

```python
width=1920      # Video width (640-3840)
height=1080     # Video height (480-2160)
fps=30          # Frames per second (15-60)
```

## Debugging

### Common Issues and Solutions

#### Issue 1: "Blender compiled without streaming support"

**Cause:** Python module missing `WITH_STREAMING` preprocessor definition

**Solution:** Add to `blender/source/blender/python/intern/CMakeLists.txt`:

```cmake
if(WITH_STREAMING)
  add_definitions(-DWITH_STREAMING)
endif()
```

#### Issue 2: "BLI_strncpy not declared"

**Cause:** Missing include for Blender string utilities

**Solution:** Add to `bpy_app_streaming.cc`:

```cpp
#include "BLI_string.h"
```

#### Issue 3: Static variable scope issues

**Cause:** Static variables declared inside functions instead of file scope

**Solution:** Move static variables to file scope (outside all functions):

```cpp
/* Shared configuration storage for streaming parameters */
static char stored_producer_id[256] = {0};
static int stored_width = 1920;
static int stored_height = 1080;
static int stored_fps = 30;
```

### Logging

**Backend logs show:**

```
INFO:...event_handlers:Starting WebRTC streaming with producer_id: blender-dreem
GStreamer GL context created successfully (platform auto-detected)
Using signaller URI: ws://127.0.0.1:8443
Viewport streaming started!
Stream name: blender-dreem
Resolution: 1920x1080 @ 30 fps
Web interface: http://localhost:9090/
INFO:...event_handlers:WebRTC streaming started successfully for dreem
```

## Testing

### Manual Test Procedure

1. **Start signaller server** (if not already running)

   ```bash
   # Start WebRTC signaller on port 8443
   ```

2. **Start backend**

   ```bash
   cd backend/cr8_engine
   python main.py
   ```

3. **Start frontend**

   ```bash
   cd frontend
   pnpm dev
   ```

4. **Test streaming**
   - Open browser to frontend URL
   - Enter username (e.g., "dreem")
   - Launch Blender instance
   - Verify stream appears in workspace
   - Check backend logs for producer ID
   - Verify producer ID matches: `blender-{username}`

### Multi-User Test

1. Open multiple browser windows
2. Use different usernames in each
3. Launch Blender for each user
4. Verify each receives their own stream
5. Verify producer IDs are unique per user

## Future Enhancements

### Potential Improvements

1. **Dynamic Resolution**

   - Allow users to configure resolution
   - Adapt to network conditions

2. **Quality Settings**

   - Bitrate control
   - FPS adjustment
   - Codec selection

3. **Stream Recording**

   - Save streams to file
   - Replay functionality

4. **Multi-Viewport**

   - Stream multiple viewports
   - Picture-in-picture support

5. **Performance Monitoring**
   - Stream quality metrics
   - Latency monitoring
   - Bandwidth usage

## Related Documentation

- [Custom Blender Build](CUSTOM_BLENDER_BUILD.md) - Building Blender with streaming support
- [GST WebRTC Setup](GST_WEBRTC_SETUP.md) - GStreamer WebRTC configuration
- [Blender Streaming Feature](../blender-git/blender-streaming-feature.md) - Original feature specification

## Conclusion

This implementation provides a robust, scalable solution for per-user WebRTC streaming in a multi-user Blender environment. The dynamic producer ID system ensures each user receives their own stream without conflicts, while the Python API provides clean integration with Blender's event system.

The key architectural decisions were:

1. **File-scoped static variables** for configuration storage
2. **CMake preprocessor definitions** for Python module compilation
3. **Environment variable passing** for username propagation
4. **Dynamic producer ID construction** on both backend and frontend

These decisions enable a maintainable, extensible streaming system that can scale to support many concurrent users.
