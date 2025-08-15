import { useState, useCallback, useEffect, useRef } from "react";
import { toast } from "sonner";
import { WebSocketMessage } from "@/lib/types/websocket";

interface PreviewRendererConfig {
  onMessage?: (data: any) => void;
}

export const usePreviewRenderer = (
  websocket: WebSocket | null,
  config?: PreviewRendererConfig
) => {
  const [isLoading, setIsLoading] = useState(false);
  const websocketRef = useRef<WebSocket | null>(websocket);
  const onMessageCallback = useRef(config?.onMessage);

  // Update refs when dependencies change
  useEffect(() => {
    websocketRef.current = websocket;
  }, [websocket]);

  useEffect(() => {
    onMessageCallback.current = config?.onMessage;
  }, [config]);

  const checkConnection = useCallback(() => {
    if (
      !websocketRef.current ||
      websocketRef.current.readyState !== WebSocket.OPEN
    ) {
      toast.error("WebSocket connection not available");
      return false;
    }
    return true;
  }, []);

  const sendMessage = useCallback(
    (message: WebSocketMessage) => {
      if (!checkConnection()) return;
      websocketRef.current!.send(JSON.stringify(message));
    },
    [checkConnection]
  );

  const generateVideo = useCallback(() => {
    if (!checkConnection()) return;

    setIsLoading(true);
    sendMessage({
      command: "generate_video",
    });
    toast.info("Starting video generation...");
  }, [checkConnection, sendMessage]);

  // Handle incoming messages
  useEffect(() => {
    if (!websocket) return;

    const handleMessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        // Handle connection acknowledgment
        if (data.status === "ACK") {
          return; // Prevent further processing of ACK messages
        }

        // Update internal states based on message type
        if (data.type === "video_generation_complete") {
          setIsLoading(false);
        }

        // Forward message to callback if provided
        if (onMessageCallback.current) {
          onMessageCallback.current(data);
        }
      } catch (error) {
        console.error("Error handling WebSocket message:", error);
        toast.error("Failed to process server message");
        setIsLoading(false);
      }
    };

    websocket.addEventListener("message", handleMessage);

    return () => {
      websocket.removeEventListener("message", handleMessage);
    };
  }, [websocket]);

  // Reset states when websocket changes
  useEffect(() => {
    if (!websocket) {
      setIsLoading(false);
    }
  }, [websocket]);

  return {
    isLoading,
    generateVideo,
  };
};
