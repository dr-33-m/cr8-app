import { useEffect, useRef, useState, useCallback } from "react";
import { io, Socket } from "socket.io-client";
import useUserStore from "@/store/userStore";
import { toast } from "sonner";
import {
  WebSocketStatus,
  WebSocketMessage,
  MessageType,
  generateMessageId,
  SocketMessage,
  CommandPayload,
  AgentQueryPayload,
} from "@/lib/types/websocket";

export const useSocketIO = (onMessage?: (data: any) => void) => {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const socketRef = useRef<Socket | null>(null);
  const onMessageCallback = useRef(onMessage);
  const isManuallyDisconnected = useRef(false);

  const { username } = useUserStore();
  const serverUrl =
    import.meta.env.VITE_WEBSOCKET_URL?.replace(/^ws/, "http") ||
    "http://localhost:8000";

  useEffect(() => {
    onMessageCallback.current = onMessage;
  }, [onMessage]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (!socketRef.current?.connected) {
      toast.error("Not connected to server");
      return;
    }

    // Generate message_id if not provided
    const message_id = message.message_id || generateMessageId();

    // Route based on command type
    const { command, route, ...data } = message;

    // Handle special browser_ready signal
    if (command === "browser_ready") {
      // Browser ready signal (no standardization needed - internal event)
      socketRef.current.emit("browser_ready", data);
      return;
    }

    // Route explicitly based on route field
    if (route === "direct") {
      // Direct command path
      const commandMessage: SocketMessage = {
        message_id,
        type: MessageType.COMMAND_SENT,
        payload: {
          addon_id: message.addon_id || "blender_ai_router",
          command: command!,
          params: message.params || data,
        } as CommandPayload,
        metadata: {
          timestamp: Date.now(),
          source: "browser",
          route: "direct",
          refresh_context: message.refresh_context ?? false, // Preserve refresh_context flag
        },
      };
      socketRef.current.emit(MessageType.COMMAND_SENT, commandMessage);
    } else if (route === "agent") {
      // Agent path
      const agentMessage: SocketMessage = {
        message_id,
        type: MessageType.AGENT_QUERY_SENT,
        payload: {
          message: message.message || "",
          context: message.context,
        } as AgentQueryPayload,
        metadata: {
          timestamp: Date.now(),
          source: "browser",
          route: "agent",
          refresh_context: message.refresh_context ?? false, // Use message value, default to false for agent
        },
      };
      socketRef.current.emit(MessageType.AGENT_QUERY_SENT, agentMessage);
    } else {
      console.error("No route specified for message:", message);
      toast.error("Invalid message format - route not specified");
    }
  }, []);

  const disconnect = useCallback(() => {
    if (socketRef.current) {
      isManuallyDisconnected.current = true;
      socketRef.current.disconnect();
      socketRef.current = null;
    }
    setStatus("disconnected");
  }, []);

  const connect = useCallback(() => {
    if (!username) {
      toast.error("Missing username");
      return;
    }

    const { fullBlendFilePath } = useUserStore.getState();

    isManuallyDisconnected.current = false;
    setStatus("connecting");

    try {
      const socket = io(`${serverUrl}/browser`, {
        path: "/ws/socket.io/",
        auth: {
          username,
          blend_file_path: fullBlendFilePath || undefined,
        },
        reconnection: true,
        reconnectionDelay: 2000,
        reconnectionDelayMax: 30000,
        reconnectionAttempts: 5,
        transports: ["websocket", "polling"],
      });

      socketRef.current = socket;

      // Connection events
      socket.on("connect", () => {
        setStatus("connected");
        isManuallyDisconnected.current = false;
      });

      socket.on("connect_error", (error) => {
        console.error("Socket.IO connection error:", error);
        if (!socket.active) {
          // Connection was denied by server
          setStatus("failed");
          toast.error("Connection denied by server");
        } else {
          // Temporary failure, will auto-retry
          setStatus("disconnected");
        }
      });

      socket.on("disconnect", (reason) => {
        console.log("Socket.IO disconnected:", reason);

        if (isManuallyDisconnected.current) {
          setStatus("disconnected");
          return;
        }

        if (
          reason === "io server disconnect" ||
          reason === "io client disconnect"
        ) {
          setStatus("disconnected");
        } else {
          // Temporary disconnection, Socket.IO will auto-reconnect
          setStatus("disconnected");
        }
      });

      // Register standardized event listeners
      const eventTypes = [
        MessageType.SESSION_CREATED,
        MessageType.SESSION_READY,
        MessageType.BLENDER_CONNECTED,
        MessageType.BLENDER_DISCONNECTED,
        MessageType.COMMAND_COMPLETED,
        MessageType.COMMAND_FAILED,
        MessageType.AGENT_RESPONSE_READY,
        MessageType.AGENT_ERROR,
        MessageType.SCENE_CONTEXT_UPDATED,
        MessageType.INBOX_CLEARED,
        MessageType.EXECUTION_ERROR,
      ];

      eventTypes.forEach((eventType) => {
        socket.on(eventType, (data) => {
          if (onMessageCallback.current) {
            onMessageCallback.current(data);
          }
        });
      });

      // Debug logger for all events
      socket.onAny((event, data) => {
        console.log(`Socket.IO event: ${event}`, data);
      });
    } catch (error) {
      console.error("Error creating Socket.IO connection:", error);
      setStatus("failed");
      toast.error("Failed to establish connection");
    }
  }, [username, serverUrl]);

  const reconnect = useCallback(() => {
    isManuallyDisconnected.current = false;
    disconnect();
    setTimeout(() => connect(), 100);
  }, [disconnect, connect]);

  useEffect(() => {
    if (username) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [username]); // Only reconnect when username changes

  return {
    status,
    socket: socketRef.current,
    isConnected: status === "connected",
    reconnect,
    disconnect,
    sendMessage,
  };
};
