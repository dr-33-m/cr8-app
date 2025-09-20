import {
  createContext,
  useContext,
  ReactNode,
  useCallback,
  useState,
  useEffect,
  useRef,
} from "react";
import { useWebSocket } from "@/hooks/useWebsocket";
import { WebSocketStatus, WebSocketMessage } from "@/lib/types/websocket";
import useSceneContextStore from "@/store/sceneContextStore";
import { toast } from "sonner";

interface WebSocketContextType {
  status: WebSocketStatus;
  websocket: WebSocket | null;
  isConnected: boolean;
  blenderConnected: boolean;
  isFullyConnected: boolean;
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

  // Use refs for immediate state tracking to avoid race conditions
  const isReconnectionRef = useRef(false);
  const shouldSendBrowserReadyRef = useRef(false);

  const processMessage = useCallback(
    (data: any) => {
      // Handle system messages
      if (data.type === "system") {
        switch (data.status) {
          case "blender_connected":
            setBlenderConnected(true);
            if (data.message?.includes("Reconnected to existing")) {
              isReconnectionRef.current = true;
              shouldSendBrowserReadyRef.current = false;
              toast.success("Reconnected to existing Blender session");
            }
            break;
          case "blender_disconnected":
            setBlenderConnected(false);
            break;
          case "waiting_for_blender":
            setBlenderConnected(false);
            toast.info(data.message || "Waiting for Blender to connect...");
            break;
          case "error":
            if (data.message?.includes("Failed to launch Blender")) {
              setBlenderConnected(false);
              toast.error(data.message);
              // Auto-recovery attempt
              setTimeout(() => {
                if (wsHook.websocket?.readyState === WebSocket.OPEN) {
                  console.log("Attempting to recover Blender connection");
                  wsHook.sendMessage({
                    command: "browser_ready",
                    recovery: true,
                  });
                }
              }, 1000);
            }
            break;
        }
      }

      // Handle scene context updates
      else if (
        data.type === "scene_context_update" &&
        data.status === "success"
      ) {
        const { objects, timestamp } = data.data;
        useSceneContextStore.getState().setSceneObjects(objects, timestamp);
        console.log("Scene context updated:", objects.length, "objects");
      }

      // Handle B.L.A.Z.E Agent responses
      if (data.status === "success") {
        const isNavigationCommand =
          data.data?.data?.navigation_action ||
          data.data?.data?.viewport_mode ||
          data.data?.data?.animation_state ||
          data.data?.data?.current_frame ||
          data.command.includes("transform_");

        if (!isNavigationCommand) {
          toast.success("B.L.A.Z.E: " + (data.message || "Action completed"));
        }
      } else if (data.status === "error") {
        toast.error("B.L.A.Z.E Error: " + (data.message || "Unknown error"));
      }

      // Forward to custom handler
      onMessage?.(data);
    },
    [onMessage]
  );

  const wsHook = useWebSocket((data: any) => {
    // Process message first
    processMessage(data);

    // Handle session creation
    if (data.status === "connected" && data.message === "Session created") {
      toast.success("Connected to Cr8 Engine");
      setSessionCreated(true);
      // Only prepare to send browser_ready for fresh connections
      if (!isReconnectionRef.current) {
        shouldSendBrowserReadyRef.current = true;
      }
    }
  });

  // Send browser_ready for fresh connections only
  useEffect(() => {
    if (
      sessionCreated &&
      shouldSendBrowserReadyRef.current &&
      wsHook.websocket?.readyState === WebSocket.OPEN &&
      !isReconnectionRef.current
    ) {
      const timeoutId = setTimeout(() => {
        console.log("Sending browser_ready signal for fresh connection");
        wsHook.sendMessage({ command: "browser_ready" });
        shouldSendBrowserReadyRef.current = false;
      }, 100);

      return () => clearTimeout(timeoutId);
    }
  }, [sessionCreated, wsHook.websocket, wsHook.sendMessage]);

  // Handle context updates for both fresh and reconnected sessions
  useEffect(() => {
    if (
      wsHook.isConnected &&
      blenderConnected &&
      !contextUpdateSent &&
      wsHook.websocket?.readyState === WebSocket.OPEN
    ) {
      const messageId = isReconnectionRef.current
        ? `reconnect_context_update_${Date.now()}`
        : `context_update_${Date.now()}`;

      console.log(
        isReconnectionRef.current
          ? "Browser reconnected, sending context update request"
          : "Sending initial context update request"
      );

      wsHook.sendMessage({
        command: "list_scene_objects",
        message_id: messageId,
      });

      setContextUpdateSent(true);
    }
  }, [
    wsHook.isConnected,
    blenderConnected,
    contextUpdateSent,
    wsHook.websocket,
    wsHook.sendMessage,
  ]);

  // Handle logout disconnection
  useEffect(() => {
    const handleLogoutDisconnect = () => {
      console.log("Logout event received, disconnecting WebSocket");
      if (wsHook.websocket) {
        wsHook.disconnect();
        setBlenderConnected(false);
        setContextUpdateSent(false);
        setSessionCreated(false);
        isReconnectionRef.current = false;
        shouldSendBrowserReadyRef.current = false;
      }
    };

    window.addEventListener("logout-disconnect", handleLogoutDisconnect);
    return () =>
      window.removeEventListener("logout-disconnect", handleLogoutDisconnect);
  }, [wsHook.websocket, wsHook.disconnect]);

  const contextValue = {
    ...wsHook,
    blenderConnected,
    isFullyConnected: wsHook.isConnected && blenderConnected,
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
