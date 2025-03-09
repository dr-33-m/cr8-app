import {
  createContext,
  useContext,
  ReactNode,
  useCallback,
  useRef,
  useState,
} from "react";
import { useWebSocket } from "@/hooks/useWebsocket";
import {
  WebSocketStatus,
  WebSocketMessage,
  AnimationResponseMessage,
} from "@/lib/types/websocket";
import { processWebSocketMessage } from "@/lib/handlers/websocketMessageHandler";
import { createAnimationHandler } from "@/hooks/useAnimationWebSocket";
import { useTemplateControlsStore } from "@/store/TemplateControlsStore";
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
  requestTemplateControls: () => void;
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
  const setControls = useTemplateControlsStore((state) => state.setControls);

  // Add state for tracking Blender connection
  const [blenderConnected, setBlenderConnected] = useState(false);
  // Add state to track if we've already reconnected to an existing Blender session
  const [alreadyReconnected, setAlreadyReconnected] = useState(false);

  // Use a ref to solve the circular dependency
  const animationHandlersRef = useRef<any>(null);

  // Define message processing function
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

      // Process the message using our handler
      processWebSocketMessage(data, {
        // Handle animation responses
        onAnimationResponse: (data: AnimationResponseMessage) => {
          if (animationHandlersRef.current) {
            animationHandlersRef.current.handleAnimationResponse(data.data);
          }
        },

        // Handle template controls response
        onTemplateControls: (data) => {
          // Check for controls in the correct location (data.data.controls)
          if (data.data?.controls) {
            // Transform flat list into categorized structure
            const categorized = {
              cameras: data.data.controls.filter(
                (c: any) => c.type === "camera"
              ),
              lights: data.data.controls.filter((c: any) => c.type === "light"),
              materials: data.data.controls.filter(
                (c: any) => c.type === "material"
              ),
              objects: data.data.controls.filter(
                (c: any) => c.type === "object"
              ),
            };
            setControls(categorized);

            // Show success toast
            toast.success("Template controls loaded");
          } else {
            console.error(
              "No controls found in template_controls_result",
              data
            );
          }
        },

        // Forward to custom handler if provided
        onCustomMessage: onMessage,
      });

      // Also forward to the original onMessage handler if provided
      if (onMessage) {
        onMessage(data);
      }
    },
    [onMessage, setControls]
  );

  // Use the WebSocket hook with our custom message handler
  const wsHookWithHandler = useWebSocket((data: any) => {
    // Process the message first to potentially set alreadyReconnected
    processMessage(data);

    // Check for initial connection confirmation
    if (data.status === "connected" && data.message === "Session created") {
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

  // Create animation handlers with the sendMessage function and store in ref
  const animationHandlers = createAnimationHandler(
    wsHookWithHandler.sendMessage
  );
  animationHandlersRef.current = animationHandlers;

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
