import { useState, useCallback, useEffect, useRef } from "react";
import { toast } from "sonner";
import { WebSocketMessage } from "@/lib/types/websocket";
import {
  createPeerConnection,
  handleICECandidateEvent,
  handleTrackEvent,
  handleAnswer,
  handleIncomingICECandidate,
  createAndSendOffer,
} from "@/lib/webrtc";

interface PreviewRendererConfig {
  onMessage?: (data: any) => void;
}

interface RTCMessage {
  command: "webrtc";
  signalType: "offer" | "answer" | "ice-candidate";
  signalData: any;
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
  const peerConnection = useRef<RTCPeerConnection | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);

  // Update refs when dependencies change
  useEffect(() => {
    websocketRef.current = websocket;
    if (!websocket) {
      setIsPlaying(false);
      setIsPreviewAvailable(false);
      if (peerConnection.current) {
        peerConnection.current.close();
        peerConnection.current = null;
      }
    }
  }, [websocket]);

  // Initialize WebRTC
  const initializeWebRTC = useCallback(async () => {
    if (!websocketRef.current) return;

    try {
      // Create new RTCPeerConnection with event handlers
      const pc = createPeerConnection();
      peerConnection.current = pc;

      // Set up event handlers
      pc.ontrack = (event) => {
        handleTrackEvent(event, videoRef.current);
        setIsPreviewAvailable(true);
        setIsLoading(false);
      };

      pc.onicecandidate = (event) => {
        if (websocketRef.current) {
          handleICECandidateEvent(event, (signal) =>
            websocketRef.current!.send(JSON.stringify(signal))
          );
        }
      };

      pc.onconnectionstatechange = () => {
        if (pc.connectionState === "failed") {
          toast.error("WebRTC connection failed, falling back to WebSocket");
          if (peerConnection.current) {
            peerConnection.current.close();
            peerConnection.current = null;
          }
        }
      };

      // Create and send offer
      await createAndSendOffer(pc, (signal) =>
        websocketRef.current!.send(JSON.stringify(signal))
      );
    } catch (error) {
      console.error("WebRTC initialization error:", error);
      toast.error(
        "Failed to initialize WebRTC connection, using WebSocket fallback"
      );
    }
  }, []);

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

  const shootPreview = useCallback(
    async (sceneConfiguration: any, resetSceneConfiguration: () => void) => {
      if (!checkConnection()) return;

      setIsLoading(true);
      setIsPreviewAvailable(false);

      try {
        // Initialize WebRTC before starting preview
        await initializeWebRTC();

        sendMessage({
          command: "start_preview_rendering",
          params: sceneConfiguration,
        });
        toast.info("Starting preview rendering...");
        resetSceneConfiguration();
      } catch (error) {
        console.error("Error starting preview:", error);
        // Continue with WebSocket fallback
        sendMessage({
          command: "start_preview_rendering",
          params: sceneConfiguration,
        });
        toast.info("Starting preview rendering (WebSocket mode)...");
        resetSceneConfiguration();
      }
    },
    [checkConnection, sendMessage, initializeWebRTC]
  );

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

    const handleMessage = async (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);

        // Handle connection acknowledgment
        if (data.status === "ACK") {
          return;
        }

        // Handle WebRTC signaling messages
        if (data.command === "webrtc") {
          const { signalType, signalData } = data;

          if (signalType === "answer" && peerConnection.current) {
            await handleAnswer(peerConnection.current, {
              sdp: signalData.sdp,
              type: signalData.type,
            });
          } else if (signalType === "ice-candidate" && peerConnection.current) {
            await handleIncomingICECandidate(peerConnection.current, {
              candidate: signalData.candidate,
              sdpMid: signalData.sdpMid,
              sdpMLineIndex: signalData.sdpMLineIndex,
            });
          }
          return;
        }

        // Update internal states based on message type
        if (data.type === "viewport_stream_error") {
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
    videoRef,
  };
};
