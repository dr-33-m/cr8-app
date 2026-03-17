import {
  createContext,
  useContext,
  ReactNode,
  useCallback,
  useState,
  useEffect,
  useRef,
} from "react";
import { useSocketIO } from "@/hooks/useSocketIO";
import {
  WebSocketStatus,
  WebSocketMessage,
  MessageType,
  SocketMessage,
  isSocketMessage,
  isResponsePayload,
} from "@/lib/types/websocket";
import useInboxStore from "@/store/inboxStore";
import { toast } from "sonner";
import { Socket } from "socket.io-client";
import { useQueryClient } from "@tanstack/react-query";
import { sceneContextKeys } from "@/websocket/query-manager/scene-context";
import { useLaunchTimerStore } from "@/store/launchTimerStore";

type ConnectionState =
  | "disconnected" // Not connected
  | "browser_connected" // Browser connected, waiting for Blender
  | "fully_connected" // Both connected
  | "blender_disconnected" // Blender crashed/closed
  | "server_unavailable" // Server down for 5+ minutes
  | "reconnecting"; // Attempting reconnect

export interface InstanceStatusError {
  reason: string;      // "timeout" | "ssh_failed" | "blender_failed" | "no_gpu" | "unknown"
  recoverable: boolean;
}

export interface InstanceStatus {
  phase: string;   // "created" | "loading" | "running" | "error" | "cancelled"
  elapsed: number; // seconds since launch started
  error?: InstanceStatusError; // present when phase === "error"
}

interface WebSocketContextType {
  status: WebSocketStatus;
  socket: Socket | null;
  isConnected: boolean;
  blenderConnected: boolean;
  isFullyConnected: boolean;
  connectionState: ConnectionState;
  isHealthCheckInProgress: boolean;
  instanceStatus: InstanceStatus | null;
  cancelLaunch: () => void;
  reconnect: () => void;
  disconnect: () => void;
  sendMessage: (message: WebSocketMessage) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
  onMessage?: (data: any) => void;
}

export function WebSocketProvider({
  children,
  onMessage,
}: WebSocketProviderProps) {
  const queryClient = useQueryClient();
  const [blenderConnected, setBlenderConnected] = useState(false);
  const [contextUpdateSent, setContextUpdateSent] = useState(false);
  const [sessionCreated, setSessionCreated] = useState(false);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");
  const [isHealthCheckInProgress, setIsHealthCheckInProgress] = useState(false);
  const [instanceStatus, setInstanceStatus] = useState<InstanceStatus | null>(null);

  // Use refs for immediate state tracking to avoid race conditions
  const isReconnectionRef = useRef(false);
  const shouldSendBrowserReadyRef = useRef(false);

  const processMessage = useCallback(
    (data: any) => {
      // Check if it's a standardized message
      if (!isSocketMessage(data)) {
        console.warn("Received non-standardized message:", data);
        onMessage?.(data);
        return;
      }

      const message = data as SocketMessage;
      const payload = message.payload;

      // Handle messages by type using switch
      switch (message.type) {
        case MessageType.SESSION_CREATED:
          toast.success("Connected to Cr8 Engine");
          setSessionCreated(true);
          setConnectionState("browser_connected");
          if (!isReconnectionRef.current) {
            shouldSendBrowserReadyRef.current = true;
          }
          break;

        case MessageType.INSTANCE_STATUS: {
          const p = payload as any;
          const phase: string = p.status ?? null;
          const backendElapsed: number = p.data?.elapsed ?? 0;

          if (phase) {
            const newStatus: InstanceStatus = { phase, elapsed: backendElapsed };
            if (phase === "error" && p.data?.reason) {
              newStatus.error = {
                reason: p.data.reason,
                recoverable: p.data.recoverable ?? true,
              };
            }
            setInstanceStatus(newStatus);

            if (phase === "error" || phase === "cancelled") {
              // Terminal — freeze and stop the timer.
              useLaunchTimerStore.getState().stop();
            } else if (phase === "retrying") {
              // New instance about to start — reset anchor so elapsed restarts from 0.
              useLaunchTimerStore.getState().stop();
            } else {
              useLaunchTimerStore.getState().seed(backendElapsed, phase);
            }
          } else if (p.data?.elapsed !== undefined) {
            // Backend omits 'status' when actual_status is null (new instance first polls).
            // Keep the timer running — backend fix handles this, but guard defensively.
            useLaunchTimerStore.getState().seed(backendElapsed, "loading");
          }
          break;
        }

        case MessageType.BLENDER_CONNECTED:
          useLaunchTimerStore.getState().stop();
          // Restart the message cycle for the blender_connected phase so the
          // "connecting camera" messages animate. Elapsed is hidden for this phase.
          useLaunchTimerStore.getState().seed(0, "blender_connected");
          setInstanceStatus({
            phase: "blender_connected",
            elapsed: instanceStatus?.elapsed ?? 0,
          });
          setBlenderConnected(true);
          setConnectionState("fully_connected");
          if (
            isResponsePayload(payload) &&
            payload.data?.message?.includes("Reconnected")
          ) {
            isReconnectionRef.current = true;
            shouldSendBrowserReadyRef.current = false;
            toast.success("Reconnected to existing Blender session");
          }
          break;

        case MessageType.BLENDER_DISCONNECTED:
          useLaunchTimerStore.getState().stop();
          setBlenderConnected(false);
          setConnectionState("blender_disconnected");
          // Clear scene context when Blender disconnects
          queryClient.setQueryData(sceneContextKeys.objects(), null);
          // Reset context update flag so it triggers on next connection
          setContextUpdateSent(false);
          if (isResponsePayload(payload)) {
            toast.info(payload.data?.message || "Blender disconnected");
          }
          break;

        case MessageType.INBOX_CLEARED:
          useInboxStore.getState().clearAll();
          toast.success("Inbox cleared successfully");
          break;

        case MessageType.COMMAND_COMPLETED:
          // Handle scene context updates from list_scene_objects command
          if (isResponsePayload(payload) && payload.status === "success") {
            // Check if this is a scene objects response (array of objects nested in data.data)
            const hasData = payload.data?.data;
            const isArray = Array.isArray(payload.data?.data);
            const hasLength = payload.data?.data?.length > 0;
            const hasFirstName = payload.data?.data?.[0]?.name;

            if (hasData && isArray && hasLength && hasFirstName) {
              // Scenario A: response IS scene data — update cache directly, no refetch
              queryClient.setQueryData(sceneContextKeys.objects(), {
                objects: payload.data.data,
                timestamp: Math.floor(Date.now() / 1000),
              });
            }
            // Scenario B: non-scene commands (transforms, viewport changes, etc.)
            // — do NOT invalidate. The 2-second polling handles scene sync.
            // Calling invalidateQueries here caused burst-firing of list_scene_objects
            // after every command, overwhelming the Blender socket.io client.
            // Remove toast.success completely - direct commands have visual feedback
            // Only agent commands should send success responses if needed
          }
          break;

        case MessageType.COMMAND_FAILED:
          if (isResponsePayload(payload) && payload.error) {
            toast.error(payload.error.user_message);
            console.error("Command failed:", payload.error.technical_message);
          }
          break;

        case MessageType.AGENT_RESPONSE_READY:
          if (isResponsePayload(payload) && payload.data?.message) {
            toast.success("B.L.A.Z.E: " + payload.data.message);
          }
          break;

        case MessageType.AGENT_ERROR:
          if (isResponsePayload(payload) && payload.error) {
            toast.error("B.L.A.Z.E: " + payload.error.user_message);
            console.error("Agent error:", payload.error.technical_message);
            if (payload.error.recovery_suggestions?.length) {
              console.info(
                "Recovery suggestions:",
                payload.error.recovery_suggestions
              );
            }
          }
          break;

        case MessageType.EXECUTION_ERROR:
          if (isResponsePayload(payload) && payload.error) {
            toast.error(payload.error.user_message);
            console.error("Execution error:", payload.error.technical_message);
          }
          break;

        default:
          console.log("Unhandled message type:", message.type);
      }

      // Forward to custom handler
      onMessage?.(data);
    },
    [onMessage]
  );

  // Define cleanup callback for when server is unavailable for 5+ minutes
  const performServerCleanup = useCallback(() => {
    console.log("Performing cleanup after 5 minutes of server downtime");

    // Clear application state
    useLaunchTimerStore.getState().stop();
    queryClient.setQueryData(sceneContextKeys.objects(), null);
    useInboxStore.getState().clearAll();

    // Update connection state
    setBlenderConnected(false);
    setConnectionState("server_unavailable");
    setContextUpdateSent(false);
    setSessionCreated(false);

    // Notify user
    toast.error("Server unavailable for 5+ minutes. Session cleared.", {
      duration: 10000,
    });
  }, [queryClient]);

  const wsHook = useSocketIO((data: any) => {
    // Process message first
    processMessage(data);

    // Handle session creation (Socket.IO connect event)
    if (data.type === "system" && data.status === "connected") {
      toast.success("Connected to Cr8 Engine");
      setSessionCreated(true);
      setConnectionState("browser_connected");
      // Only prepare to send browser_ready for fresh connections
      if (!isReconnectionRef.current) {
        shouldSendBrowserReadyRef.current = true;
      }
    }
  }, performServerCleanup);

  // Check server health endpoint
  const checkServerHealth = useCallback(async (): Promise<boolean> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);

      const response = await fetch("http://localhost:8000/health", {
        method: "GET",
        signal: controller.signal,
      });

      clearTimeout(timeoutId);
      return response.ok;
    } catch (error) {
      console.error("Health check failed:", error);
      return false;
    }
  }, []);

  // Hybrid reconnect: handles both Blender relaunch and full server reconnection
  const reconnect = useCallback(async () => {
    // If socket is connected but Blender is not, send browser_ready signal to relaunch Blender
    if (
      wsHook.socket?.connected &&
      connectionState === "blender_disconnected"
    ) {
      setConnectionState("reconnecting");
      console.log("Sending browser_ready signal to relaunch Blender");
      wsHook.socket.emit("browser_ready", { recovery: true });
    } else if (
      connectionState === "server_unavailable" ||
      connectionState === "disconnected"
    ) {
      // Check if server is back online before attempting reconnect (for both server_unavailable and disconnected states)
      console.log(`Server was ${connectionState}, checking health endpoint...`);
      setIsHealthCheckInProgress(true);
      try {
        const isHealthy = await checkServerHealth();
        if (!isHealthy) {
          toast.error("Server still unavailable");
          return;
        }
        // Server is healthy, proceed with reconnect
        console.log("Server is healthy, attempting reconnect");
        wsHook.reconnect();
      } finally {
        setIsHealthCheckInProgress(false);
      }
    } else {
      // Otherwise, do full reconnect cycle (for general disconnection)
      console.log("Performing full reconnect cycle");
      wsHook.reconnect();
    }
  }, [wsHook.socket, wsHook.reconnect, connectionState, checkServerHealth]);

  // Send browser_ready for fresh connections only
  useEffect(() => {
    if (
      sessionCreated &&
      shouldSendBrowserReadyRef.current &&
      wsHook.socket?.connected &&
      !isReconnectionRef.current
    ) {
      const timeoutId = setTimeout(() => {
        console.log("Sending browser_ready signal for fresh connection");
        wsHook.sendMessage({ command: "browser_ready" });
        shouldSendBrowserReadyRef.current = false;
      }, 100);

      return () => clearTimeout(timeoutId);
    }
  }, [sessionCreated, wsHook.socket, wsHook.sendMessage]);

  // Handle context updates for both fresh and reconnected sessions
  useEffect(() => {
    if (
      wsHook.isConnected &&
      blenderConnected &&
      !contextUpdateSent &&
      wsHook.socket?.connected
    ) {
      const messageId = isReconnectionRef.current
        ? `reconnect_context_update_${Date.now()}`
        : `context_update_${Date.now()}`;

      console.log(
        isReconnectionRef.current
          ? "Browser reconnected, sending context update request"
          : "Sending initial context update request"
      );

      wsHook.socket?.emit("command_sent", {
        message_id: messageId,
        type: "command_sent",
        payload: {
          addon_id: "multi_registry_assets",
          command: "list_scene_objects",
          params: {},
        },
        metadata: {
          route: "direct",
          source: "browser",
        },
      });

      setContextUpdateSent(true);
    }
  }, [
    wsHook.isConnected,
    blenderConnected,
    contextUpdateSent,
    wsHook.socket,
    wsHook.sendMessage,
  ]);

  // Stop the launch timer when the workspace unmounts (navigation away).
  useEffect(() => {
    return () => {
      useLaunchTimerStore.getState().stop();
    };
  }, []);

  // Handle logout disconnection
  useEffect(() => {
    const handleLogoutDisconnect = () => {
      console.log("Logout event received, disconnecting Socket.IO");
      if (wsHook.socket) {
        wsHook.disconnect();
        setBlenderConnected(false);
        setContextUpdateSent(false);
        setSessionCreated(false);
        setConnectionState("disconnected");
        isReconnectionRef.current = false;
        shouldSendBrowserReadyRef.current = false;
      }
    };

    window.addEventListener("logout-disconnect", handleLogoutDisconnect);
    return () =>
      window.removeEventListener("logout-disconnect", handleLogoutDisconnect);
  }, [wsHook.socket, wsHook.disconnect]);

  // Handle initial connection failure
  useEffect(() => {
    // Only show toast for initial connection failures (not reconnections)
    if (
      wsHook.status === "failed" &&
      connectionState === "disconnected" &&
      !isReconnectionRef.current
    ) {
      console.log("Initial connection failed, checking server health...");
      checkServerHealth().then((isHealthy) => {
        if (!isHealthy) {
          toast.error(
            "Cannot connect to server - Please check if Cr8 Engine is running"
          );
        }
      });
    }
  }, [wsHook.status, connectionState, checkServerHealth]);

  const cancelLaunch = useCallback(() => {
    if (wsHook.socket?.connected) {
      wsHook.socket.emit("cancel_launch");
      setInstanceStatus({
        phase: "cancelled",
        elapsed: instanceStatus?.elapsed ?? 0,
      });
    }
  }, [wsHook.socket, instanceStatus]);

  const contextValue = {
    ...wsHook,
    blenderConnected,
    isFullyConnected: wsHook.isConnected && blenderConnected,
    connectionState,
    isHealthCheckInProgress,
    instanceStatus,
    cancelLaunch,
    reconnect,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error(
      "useWebSocketContext must be used within a WebSocketProvider"
    );
  }
  return context;
}
