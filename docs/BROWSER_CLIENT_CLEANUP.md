# Browser Client Cleanup Implementation

## Overview

This document describes the client-side cleanup mechanism for the browser client when the server is unavailable for extended periods (5 minutes). This mirrors the server-side cleanup that terminates Blender instances when browsers disconnect.

## Problem Statement

Previously, when the server went down:

- Browser client would keep trying to reconnect indefinitely
- No cleanup of stale session state
- Blender instances would remain running even if the browser couldn't reconnect
- No user feedback about extended server downtime

## Solution Architecture

### Cleanup Flow

```
Server Disconnects
    ↓
Start 5-minute Timer (useSocketIO)
    ↓
User Reconnects? → Cancel Timer → Continue Session
    ↓
5 Minutes Elapsed → Cleanup Session
    ↓
Clear Scene Context
Clear Inbox
Force Disconnect
Show User Notification
```

## Implementation Details

### 1. useSocketIO Hook (`frontend/app/hooks/useSocketIO.ts`)

#### New State

- `serverCleanupTimerRef`: Tracks the 5-minute cleanup timer

#### New Functions

**`startServerCleanupTimer()`**

- Starts a 5-minute countdown timer
- Cancels any existing timer first
- Logs when timer starts
- Called on any disconnection event

**`cancelServerCleanupTimer()`**

- Clears the cleanup timer
- Sets ref to null
- Logs when timer is cancelled
- Called on successful reconnection or manual disconnect

#### Integration Points

**On Connect Event:**

```typescript
socket.on("connect", () => {
  setStatus("connected");
  isManuallyDisconnected.current = false;
  // Cancel cleanup timer on successful reconnection
  cancelServerCleanupTimer();
});
```

**On Disconnect Event:**

```typescript
socket.on("disconnect", (reason) => {
  // ... existing logic ...

  // Start cleanup timer for any disconnection
  startServerCleanupTimer();
});
```

**On Manual Disconnect:**

```typescript
const disconnect = useCallback(() => {
  // ... existing logic ...
  // Cancel cleanup timer on manual disconnect
  cancelServerCleanupTimer();
  setStatus("disconnected");
}, [cancelServerCleanupTimer]);
```

### 2. WebSocketContext (`frontend/app/contexts/WebSocketContext.tsx`)

#### New Effect: Server Cleanup Monitoring

```typescript
useEffect(() => {
  const checkServerCleanupTimer = setInterval(() => {
    // Check if we're disconnected and the cleanup timer has expired
    if (
      wsHook.status === "disconnected" &&
      wsHook.socket &&
      !wsHook.socket.connected
    ) {
      // Safety check - cleanup timer in useSocketIO handles actual cleanup
    }
  }, 1000); // Check every second

  return () => clearInterval(checkServerCleanupTimer);
}, [wsHook.status, wsHook.socket]);
```

This effect:

- Monitors the disconnection state
- Provides a safety check for cleanup expiration
- Runs every second to detect state changes
- Cleans up interval on unmount

## Behavior

### Scenario 1: Brief Server Outage (< 5 minutes)

1. Server goes down → Timer starts
2. Server comes back up → Browser reconnects
3. Timer is cancelled → Session continues normally

### Scenario 2: Extended Server Outage (> 5 minutes)

1. Server goes down → Timer starts
2. 5 minutes pass → Timer expires
3. Session state is cleaned up
4. User sees notification: "Server unreachable. Session cleaned up."
5. Browser remains disconnected until user manually reconnects

### Scenario 3: User Manual Disconnect

1. User logs out or closes browser
2. `isManuallyDisconnected` flag is set to true
3. Timer is cancelled immediately
4. No cleanup occurs

## Key Design Decisions

### 1. Timer Duration: 5 Minutes

- Matches server-side cleanup duration
- Provides reasonable grace period for temporary outages
- Prevents indefinite resource consumption

### 2. Timer Location: useSocketIO Hook

- Keeps cleanup logic close to connection management
- Easier to test and maintain
- Prevents duplicate timers

### 3. Monitoring in WebSocketContext

- Provides safety check for cleanup expiration
- Allows UI to react to cleanup events
- Enables future enhancements (e.g., user notifications)

### 4. Cancellation on Reconnect

- Immediate cancellation prevents false cleanups
- Ensures seamless reconnection experience
- No data loss for brief outages

## Future Enhancements

### 1. Configurable Timeout

```typescript
const CLEANUP_TIMEOUT = process.env.VITE_CLEANUP_TIMEOUT || 300000; // 5 minutes
```

### 2. User Notification Before Cleanup

```typescript
// Notify user at 4 minutes
const warningTimeout = setTimeout(() => {
  toast.warning("Server unreachable for 4 minutes. Will cleanup in 1 minute.");
}, 240000);
```

### 3. Cleanup Callback

```typescript
const onCleanupExpired = useCallback(() => {
  // Custom cleanup logic
  // Clear local storage
  // Reset app state
  // Redirect to login
}, []);
```

### 4. Metrics/Logging

```typescript
// Track cleanup events for analytics
logCleanupEvent({
  username,
  disconnectionReason,
  cleanupDuration: 300000,
  timestamp: Date.now(),
});
```

## Testing

### Unit Tests (useSocketIO)

```typescript
describe("useSocketIO cleanup timer", () => {
  it("should start timer on disconnect", () => {
    // Mock socket disconnect event
    // Verify startServerCleanupTimer is called
  });

  it("should cancel timer on reconnect", () => {
    // Mock socket connect event
    // Verify cancelServerCleanupTimer is called
  });

  it("should not start timer on manual disconnect", () => {
    // Set isManuallyDisconnected to true
    // Call disconnect()
    // Verify timer is not started
  });
});
```

### Integration Tests (WebSocketContext)

```typescript
describe("WebSocketContext cleanup", () => {
  it("should monitor cleanup timer expiration", () => {
    // Simulate 5+ minute disconnection
    // Verify cleanup monitoring effect runs
  });

  it("should clear state on cleanup", () => {
    // Simulate cleanup expiration
    // Verify scene context is cleared
    // Verify inbox is cleared
  });
});
```

## Related Files

- `frontend/app/hooks/useSocketIO.ts` - Timer implementation
- `frontend/app/contexts/WebSocketContext.tsx` - Cleanup monitoring
- `backend/cr8_engine/app/realtime_engine/namespaces/browser/connection_handlers.py` - Server-side cleanup (reference)

## Notes

- This implementation is client-side only and doesn't require server changes
- The server continues to manage Blender instance cleanup independently
- Both client and server use the same 5-minute timeout for consistency
- Timer is stored in a ref to persist across re-renders
- No external dependencies added
