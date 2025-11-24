## Brief overview

Guidelines for building maintainable WebSocket-based server state management with React Query, following the same architectural patterns as our HTTP-based server state but adapted for real-time WebSocket data.

## Core Architecture Pattern

WebSocket server state follows a three-layer architecture similar to HTTP server state but with WebSocket-specific adaptations:

```
WebSocket Commands → Query Manager → React Query Hook
       ↓
Promise-based WebSocket utilities (not HTTP server functions)
```

## Key Principles

### 1. Promise-Based WebSocket Commands

React Query's `queryFn` expects a Promise. Since WebSockets are event-driven, we create promise-based wrappers:

```typescript
// websocket/commands/sceneContext.ts
export function createSceneObjectsCommand(socket: Socket | null) {
  return (): Promise<SceneObjectsResponse> => {
    return new Promise((resolve, reject) => {
      // Send command and wait for specific response
      socket.emit("command_sent", { message_id: uniqueId, ... });
      socket.once(`response_${uniqueId}`, handleResponse);
    });
  };
}
```

### 2. Same Query Manager Structure

Follow the exact same pattern as HTTP queries:

```typescript
// websocket/query-manager/scene-context/keys.ts
export const sceneContextKeys = {
  all: ["scene-context"] as const,
  objects: () => [...sceneContextKeys.all, "objects"] as const,
};

// websocket/query-manager/scene-context/options.ts
export function createSceneObjectsQueryOptions(
  commandFn: () => Promise<SceneObjectsResponse>
) {
  return {
    queryKey: sceneContextKeys.objects(),
    queryFn: commandFn,
    staleTime: 0, // Always stale for real-time data
    refetchInterval: 2000, // Polling backup
    // ... other options
  } satisfies UseQueryOptions<SceneObjectsResponse>;
}
```

### 3. Consumer Hooks

Same pattern as HTTP hooks:

```typescript
// hooks/useSceneContext.ts
export function useSceneContext() {
  const { socket, isFullyConnected } = useWebSocketContext();
  const commandFn = createSceneObjectsCommand(socket);

  const { data, isLoading, error } = useQuery({
    ...createSceneObjectsQueryOptions(commandFn),
    enabled: isFullyConnected,
  });

  return {
    objects: data?.objects ?? [],
    timestamp: data?.timestamp ?? 0,
    loading: isLoading,
    error: error?.message,
    getObjectByName: (name: string) =>
      data?.objects.find((obj) => obj.name === name),
  };
}
```

## WebSocket Event Integration

### Hybrid Sync Pattern

Combine three mechanisms for perfect real-time sync:

1. **Direct Cache Updates** - For commands with `refresh_context=true`
2. **Event Invalidation** - For commands without refresh_context
3. **Polling Backup** - Catches missed updates

```typescript
// In WebSocketContext.tsx
case MessageType.COMMAND_COMPLETED:
  if (hasFreshSceneData) {
    // Command had refresh_context=true - use fresh data directly
    queryClient.setQueryData(sceneContextKeys.objects(), freshData);
  } else {
    // Command didn't refresh - trigger fetch
    queryClient.invalidateQueries({ queryKey: sceneContextKeys.objects() });
  }
  break;
```

## Implementation Workflow

### 1. Create WebSocket Command Utilities

- Location: `frontend/app/websocket/commands/`
- Purpose: Promise-based wrappers for WebSocket commands
- Pattern: One file per domain (sceneContext.ts, inbox.ts, etc.)

### 2. Create Query Manager

- Location: `frontend/app/websocket/query-manager/[domain]/`
- Files: `keys.ts`, `options.ts`, `index.ts`
- Follow exact same structure as HTTP query managers

### 3. Create Consumer Hook

- Location: `frontend/app/hooks/use[Domain].ts`
- Pattern: Same as HTTP hooks but with WebSocket command functions

### 4. Integrate WebSocket Events

- Location: `frontend/app/contexts/WebSocketContext.tsx`
- Add `setQueryData` for fresh data scenarios
- Add `invalidateQueries` for stale data scenarios
- Clear cache on disconnect events

## Best Practices

### Connection State Management

```typescript
const { data, isLoading, error } = useQuery({
  ...createSceneObjectsQueryOptions(commandFn),
  enabled: isFullyConnected, // Only fetch when WebSocket connected
});
```

### Immutability (From TanStack Query Docs)

```typescript
// ✅ CORRECT - Immutable update
queryClient.setQueryData(sceneContextKeys.objects(), {
  objects: newData,
  timestamp: Date.now(),
});

// ❌ WRONG - Don't mutate existing data
queryClient.setQueryData(sceneContextKeys.objects(), (oldData) => {
  oldData.objects = newData; // DON'T DO THIS
  return oldData;
});
```

### Error Handling

```typescript
export function createSceneObjectsCommand(socket: Socket | null) {
  return (): Promise<SceneObjectsResponse> => {
    if (!socket?.connected) {
      return Promise.reject(new Error("WebSocket not connected"));
    }

    return new Promise((resolve, reject) => {
      const timeout = setTimeout(() => {
        reject(new Error("Query timeout"));
      }, 5000);

      // Handle response...
    });
  };
}
```

## Benefits

✅ **Consistent Architecture**: Same patterns as HTTP server state
✅ **Real-time Updates**: WebSocket events for instant sync
✅ **Reliable Backup**: Polling catches missed events
✅ **Smart Deduplication**: React Query prevents double fetches
✅ **Type Safety**: Full TypeScript support
✅ **Loading States**: Built-in loading/error states
✅ **Caching**: Automatic cache management
✅ **Refetching**: Background refetch on window focus/reconnect

## When to Use This Pattern

### ✅ Good For:

- Real-time scene data that changes frequently
- WebSocket commands that return data
- State that needs to stay synchronized with backend
- Data that benefits from both events and polling

### ❌ Not For:

- One-time WebSocket events (use useEffect + socket.on)
- Simple notifications (use toast messages)
- Data that doesn't need caching (use direct socket calls)

## Example Implementation

See the scene context migration for a complete working example:

- `frontend/app/websocket/commands/sceneContext.ts` - WebSocket command utilities
- `frontend/app/websocket/query-manager/scene-context/` - Query configuration
- `frontend/app/hooks/useSceneContext.ts` - Consumer hook
- `frontend/app/contexts/WebSocketContext.tsx` - Event integration
