import {
  createContext,
  useContext,
  ReactNode,
  useCallback,
  useState,
  useEffect,
} from "react";
import { useWebSocket } from "@/hooks/useWebsocket";
import { WebSocketStatus, WebSocketMessage } from "@/lib/types/websocket";
import { toast } from "sonner";

interface WebSocketContextType {
  status: WebSocketStatus;
  websocket: WebSocket | null;
  isConnected: boolean; // Browser connection only
  blenderConnected: boolean; // Blender connection only
  isFullyConnected: boolean; // Both browser and Blender are connected
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
  // Add state for tracking Blender connection
  const [blenderConnected, setBlenderConnected] = useState(false);
  // Add state to track if we've already reconnected to an existing Blender session
  const [alreadyReconnected, setAlreadyReconnected] = useState(false);

  // Define simplified message processing function
  const processMessage = useCallback(
    (data: any) => {
      // Check for Blender connection/disconnection messages
      if (data.type === "system" && data.status === "blender_connected") {
        setBlenderConnected(true);
        // Show reconnection message if it's a reconnection to existing instance
        if (data.message?.includes("Reconnected to existing")) {
          setAlreadyReconnected(true);
          toast.success("Reconnected to existing Blender session");
        }
      } else if (
        data.type === "system" &&
        data.status === "blender_disconnected"
      ) {
        setBlenderConnected(false);
      } else if (
        data.type === "system" &&
        data.status === "waiting_for_blender"
      ) {
        setBlenderConnected(false);
        toast.info(data.message || "Waiting for Blender to connect...");
      } else if (
        data.type === "system" &&
        data.status === "error" &&
        data.message?.includes("Failed to launch Blender")
      ) {
        setBlenderConnected(false);
        toast.error(data.message);

        // Attempt auto-recovery after a short delay
        setTimeout(() => {
          if (wsHookWithHandler.websocket?.readyState === WebSocket.OPEN) {
            console.log("Attempting to recover Blender connection");
            wsHookWithHandler.sendMessage({
              command: "browser_ready",
              recovery: true,
            });
          }
        }, 1000);
      }

      // Handle B.L.A.Z.E Agent responses
      if (data.status === "success") {
        toast.success("B.L.A.Z.E: " + (data.message || "Action completed"));
      } else if (data.status === "error") {
        toast.error("B.L.A.Z.E Error: " + (data.message || "Unknown error"));
      }

      // Forward to custom handler if provided
      if (onMessage) {
        onMessage(data);
      }
    },
    [onMessage]
  );

  // Use the WebSocket hook with our custom message handler
  const wsHookWithHandler = useWebSocket((data: any) => {
    // Process the message first to potentially set alreadyReconnected
    processMessage(data);

    // Check for initial connection confirmation
    if (data.status === "connected" && data.message === "Session created") {
      // Show connection toast
      toast.success("Connected to Cr8 Engine");

      // Signal that browser is ready for Blender to connect, but only if we haven't already reconnected
      setTimeout(() => {
        if (
          !alreadyReconnected &&
          wsHookWithHandler.websocket?.readyState === WebSocket.OPEN
        ) {
          console.log("Sending browser_ready signal");
          wsHookWithHandler.sendMessage({
            command: "browser_ready",
          });
        } else if (alreadyReconnected) {
          console.log(
            "Skipping browser_ready signal - already reconnected to Blender"
          );
        }
      }, 500); // Small delay to ensure everything is set up
    }
  });

  // Listen for logout events to disconnect WebSocket
  useEffect(() => {
    const handleLogoutDisconnect = () => {
      console.log("Logout event received, disconnecting WebSocket");
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
  }, [wsHookWithHandler.websocket, wsHookWithHandler.disconnect]);

  // Create the context value with the combined connection state
  const contextValue = {
    ...wsHookWithHandler,
    blenderConnected,
    isFullyConnected: wsHookWithHandler.isConnected && blenderConnected,
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
