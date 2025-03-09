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
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPreviewAvailable, setIsPreviewAvailable] = useState(false);
  const websocketRef = useRef<WebSocket | null>(websocket);
  const onMessageCallback = useRef(config?.onMessage);

  // Update refs when dependencies change
  useEffect(() => {
    websocketRef.current = websocket;
    if (!websocket) {
      setIsPlaying(false);
      setIsPreviewAvailable(false);
    }
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

  const shootPreview = useCallback(() => {
    if (!checkConnection()) return;

    setIsLoading(true);
    setIsPreviewAvailable(false);
    sendMessage({
      command: "start_preview_rendering",
      params: {}, // Empty params since scene updates are sent separately
    });
    toast.info("Starting preview rendering...");
  }, [checkConnection, sendMessage]);

  const playbackPreview = useCallback(() => {
    if (!checkConnection()) return;

    setIsPlaying(true);
    sendMessage({
      command: "start_broadcast",
    });
    toast.info("Starting preview playback");
  }, [checkConnection, sendMessage]);

  const stopPlaybackPreview = useCallback(() => {
    if (!checkConnection()) return;

    setIsPlaying(false);
    sendMessage({
      command: "stop_broadcast",
    });
    toast.info("Stopping preview playback");
  }, [checkConnection, sendMessage]);

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
        if (data.type === "frame") {
          setIsPreviewAvailable(true);
          setIsLoading(false);
        } else if (data.type === "viewport_stream_error") {
          setIsLoading(false);
          setIsPlaying(false);
        } else if (data.type === "broadcast_complete") {
          setIsPlaying(false);
        } else if (data.type === "video_generation_complete") {
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
        setIsPlaying(false);
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
      setIsPlaying(false);
      setIsPreviewAvailable(false);
    }
  }, [websocket]);

  return {
    isLoading,
    isPlaying,
    isPreviewAvailable,
    shootPreview,
    playbackPreview,
    stopPlaybackPreview,
    generateVideo,
  };
};
