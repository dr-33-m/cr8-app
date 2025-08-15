# State Management Reset System

## Overview

The Cr8-xyz application now includes a comprehensive state reset system that ensures complete cleanup of application state during logout or session termination. This system provides robust state management with proper cleanup to prevent data leakage between user sessions.

## Components

### 1. Store Reset Methods

All Zustand stores now include a `reset()` method that restores the store to its initial state:

#### User Store (`useUserStore`)

```typescript
reset: () =>
  set({
    username: "",
    isAuthenticated: false,
    preferences: {
      theme: "dark",
      autoSave: true,
    },
  });
```

#### Animation Store (`useAnimationStore`)

```typescript
reset: () =>
  set({
    animations: { camera: [], light: [], product: [] },
    isLoading: false,
    error: null,
    selectedAnimations: { camera: null, light: null, product: null },
  });
```

#### Asset Placer Store (`useAssetPlacerStore`)

```typescript
reset: () =>
  set({
    availableAssets: STATIC_ASSETS,
    placedAssets: [],
    selectedAssetId: null,
  });
```

#### Template Controls Store (`useTemplateControlsStore`)

```typescript
reset: () =>
  set({
    controls: null,
    isLoading: false,
    error: null,
  });
```

#### Visibility Store (`useVisibilityStore`)

```typescript
reset: () =>
  set({
    isSceneControlsVisible: true,
    isAssetSelectionVisible: true,
    isBottomControlsVisible: true,
    isFullscreen: false,
  });
```

### 2. Logout Service

The centralized logout service (`frontend/lib/services/logoutService.ts`) provides two approaches:

#### Class-based Service (Singleton)

```typescript
const logoutService = LogoutService.getInstance();
await logoutService.performLogout();
```

#### React Hook

```typescript
const logout = useLogout();
await logout();
```

### 3. Logout Process

The complete logout process includes:

1. **Store Reset**: All Zustand stores are reset to initial state
2. **LocalStorage Cleanup**: Persisted data is removed from localStorage
3. **WebSocket Disconnection**: Active WebSocket connections are closed
4. **Navigation**: User is redirected to home page
5. **User Feedback**: Success/error messages are displayed

### 4. WebSocket Integration

The WebSocket context listens for logout events:

```typescript
useEffect(() => {
  const handleLogoutDisconnect = () => {
    if (wsHookWithHandler.websocket) {
      wsHookWithHandler.disconnect();
      setBlenderConnected(false);
      setAlreadyReconnected(false);
    }
  };

  window.addEventListener("logout-disconnect", handleLogoutDisconnect);
  return () => {
    window.removeEventListener("logout-disconnect", handleLogoutDisconnect);
  };
}, []);
```

## Usage Examples

### Basic Logout

```typescript
import { useLogout } from "@/lib/services/logoutService";

const MyComponent = () => {
  const logout = useLogout();

  const handleLogout = async () => {
    await logout();
  };

  return <button onClick={handleLogout}>Logout</button>;
};
```

### Manual Store Reset

```typescript
import useUserStore from "@/store/userStore";
import { useAnimationStore } from "@/store/animationStore";

// Reset individual stores
useUserStore.getState().reset();
useAnimationStore.getState().reset();
```

### Custom Cleanup

```typescript
import { LogoutService } from "@/lib/services/logoutService";

const performCustomCleanup = async () => {
  const logoutService = LogoutService.getInstance();
  await logoutService.performLogout();

  // Additional custom cleanup logic
  customCleanupFunction();
};
```

## Benefits

1. **Security**: Ensures no sensitive data persists between sessions
2. **Performance**: Prevents memory leaks from accumulated state
3. **Reliability**: Consistent application state on fresh sessions
4. **User Experience**: Clean slate for each user session
5. **Development**: Easier debugging with predictable initial state

## Best Practices

1. **Always use the logout service** instead of manual state clearing
2. **Test logout functionality** to ensure complete state reset
3. **Monitor localStorage** to verify proper cleanup
4. **Handle errors gracefully** during logout process
5. **Provide user feedback** for logout actions

## Error Handling

The logout service includes comprehensive error handling:

```typescript
try {
  await logout();
} catch (error) {
  console.error("Logout failed:", error);
  toast.error("Error during logout. Please refresh the page.");
}
```

## Testing

To test the reset system:

1. **Login and use the application** to populate stores
2. **Logout using the navbar menu**
3. **Verify all stores are reset** to initial state
4. **Check localStorage** is cleared
5. **Confirm WebSocket disconnection**
6. **Verify navigation** to home page

## Future Enhancements

Potential improvements to the reset system:

1. **Selective Reset**: Reset only specific parts of the application
2. **Reset Confirmation**: Ask user confirmation before logout
3. **Background Cleanup**: Periodic cleanup of unused data
4. **Reset Analytics**: Track reset operations for debugging
5. **Custom Reset Hooks**: Store-specific reset behaviors
