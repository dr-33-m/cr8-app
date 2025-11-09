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
import useSceneContextStore from "@/store/sceneContextStore";
import useInboxStore from "@/store/inboxStore";
import { toast } from "sonner";
import { Socket } from "socket.io-client";

type ConnectionState =
  | "disconnected" // Not connected
  | "browser_connected" // Browser connected, waiting for Blender
  | "fully_connected" // Both connected
  | "blender_disconnected" // Blender crashed/closed
  | "reconnecting"; // Attempting reconnect

interface WebSocketContextType {
  status: WebSocketStatus;
  socket: Socket | null;
  isConnected: boolean;
  blenderConnected: boolean;
  isFullyConnected: boolean;
  connectionState: ConnectionState;
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
  const [blenderConnected, setBlenderConnected] = useState(false);
  const [contextUpdateSent, setContextUpdateSent] = useState(false);
  const [sessionCreated, setSessionCreated] = useState(false);
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("disconnected");

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

        case MessageType.BLENDER_CONNECTED:
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
          setBlenderConnected(false);
          setConnectionState("blender_disconnected");
          // Clear scene context when Blender disconnects
          useSceneContextStore.getState().clearSceneObjects();
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
              const objects = payload.data.data;
              const timestamp = Math.floor(Date.now() / 1000); // Store as seconds to match component expectations
              useSceneContextStore
                .getState()
                .setSceneObjects(objects, timestamp);
            }
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
  });

  const reconnect = useCallback(() => {
    if (wsHook.socket?.connected) {
      setConnectionState("reconnecting");
      console.log("Sending browser_ready signal for reconnection");
      wsHook.socket.emit("browser_ready", { recovery: true });
    }
  }, [wsHook.socket]);

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

  const contextValue = {
    ...wsHook,
    blenderConnected,
    isFullyConnected: wsHook.isConnected && blenderConnected,
    connectionState,
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
