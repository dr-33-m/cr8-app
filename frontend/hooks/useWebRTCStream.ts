import { useEffect, useRef, useState, useCallback } from "react";

const PRODUCER_ID = import.meta.env.VITE_WEBRTC_PRODUCER_ID;
const SIGNALLING_SERVER_URL = import.meta.env.VITE_WEBRTC_SIGNALING_SERVER_URL;

// Define types locally since they're not exported
interface ConnectionListener {
  connected: (clientId: string) => void;
  disconnected: () => void;
}

interface PeerListener {
  producerAdded?: (producer: Peer) => void;
  producerRemoved?: (producer: Peer) => void;
  consumerAdded?: (consumer: Peer) => void;
  consumerRemoved?: (consumer: Peer) => void;
}

interface Peer {
  readonly id: string;
  readonly meta: Record<string, unknown>;
}

export function useWebRTCStream() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const [isClient, setIsClient] = useState(false);

  // Use refs to avoid dependency issues
  const webrtcApi = useRef<any>(null);
  const consumerSessionRef = useRef<any>(null);
  const GstWebRTCAPIRef = useRef<any>(null);
  const isConnectedRef = useRef(false);
  const isConnectingRef = useRef(false);

  // Check if we're on the client side
  useEffect(() => {
    setIsClient(true);
  }, []);

  // Sync refs with state
  useEffect(() => {
    isConnectedRef.current = isConnected;
  }, [isConnected]);

  useEffect(() => {
    isConnectingRef.current = isConnecting;
  }, [isConnecting]);

  const connectToProducer = useCallback((producerId: string) => {
    // Check if already connected or connecting using refs
    if (isConnectedRef.current || isConnectingRef.current) {
      return;
    }

    if (!webrtcApi.current) {
      console.error("WebRTC API not available");
      return;
    }

    setIsConnecting(true);

    const consumerSession = webrtcApi.current.createConsumerSession(producerId);
    consumerSessionRef.current = consumerSession;

    // Listen for the primary stream event
    consumerSession.addEventListener("streamsChanged", () => {
      const streams = consumerSession.streams;

      if (videoRef.current && streams && streams.length > 0) {
        videoRef.current.srcObject = streams[0];
        videoRef.current.play().catch(() => {
          // Video play failed - this is often normal due to autoplay policies
        });
        setIsConnected(true);
        setIsConnecting(false);
        console.info("WebRTC stream connected");
      }
    });

    // Listen for session closure
    consumerSession.addEventListener("closed", () => {
      setIsConnected(false);
      setIsConnecting(false);
    });

    // Listen for errors
    consumerSession.addEventListener("error", (event: any) => {
      console.error("WebRTC consumer session error:", event);
      setIsConnected(false);
      setIsConnecting(false);
    });

    // Also listen to the RTCPeerConnection events directly
    const checkForRTCPeerConnection = () => {
      if (consumerSession.rtcPeerConnection) {
        const pc = consumerSession.rtcPeerConnection;

        pc.addEventListener("track", (event: any) => {
          if (event.streams && event.streams.length > 0 && videoRef.current) {
            videoRef.current.srcObject = event.streams[0];
            setIsConnected(true);
            setIsConnecting(false);
          }
        });

        pc.addEventListener("connectionstatechange", () => {
          if (
            pc.connectionState === "failed" ||
            pc.connectionState === "disconnected"
          ) {
            setIsConnected(false);
            setIsConnecting(false);
          }
        });
      } else {
        // Retry checking for RTCPeerConnection
        setTimeout(checkForRTCPeerConnection, 100);
      }
    };

    // Start checking for RTCPeerConnection
    setTimeout(checkForRTCPeerConnection, 100);

    consumerSession.connect();
  }, []);

  // Initialize WebRTC only once when client is ready
  useEffect(() => {
    // Only run on client side and only once
    if (!isClient || webrtcApi.current) return;

    const initializeWebRTC = async () => {
      try {
        // Dynamic import to avoid SSR issues
        const { default: GstWebRTCAPI } = await import("@dr33m/gstwebrtc-api");
        GstWebRTCAPIRef.current = GstWebRTCAPI;

        setupWebRTC();
      } catch (error) {
        console.error("Failed to load GstWebRTCAPI:", error);
      }
    };

    const setupWebRTC = () => {
      if (!GstWebRTCAPIRef.current || webrtcApi.current) return;

      webrtcApi.current = new GstWebRTCAPIRef.current({
        meta: {},
        signalingServerUrl: SIGNALLING_SERVER_URL,
        reconnectionTimeout: 5000,
        webrtcConfig: {},
      });

      const connectionListener: ConnectionListener = {
        connected: (clientId: string) => {
          console.info("Connected to WebRTC signaling server");

          if (webrtcApi.current) {
            const producers = webrtcApi.current.getAvailableProducers();
            const producer = producers.find(
              (p: Peer) => p.meta.name === PRODUCER_ID
            );
            if (producer) {
              connectToProducer(producer.id);
            }
          }
        },
        disconnected: () => {
          console.warn("Disconnected from WebRTC signaling server");
          setIsConnected(false);
          setIsConnecting(false);
        },
      };

      const peerListener: PeerListener = {
        producerAdded: (producer: Peer) => {
          if (producer.meta.name === PRODUCER_ID) {
            connectToProducer(producer.id);
          }
        },
        producerRemoved: (producer: Peer) => {
          if (producer.meta.name === PRODUCER_ID) {
            setIsConnected(false);
          }
        },
      };

      webrtcApi.current.registerConnectionListener(connectionListener);
      webrtcApi.current.registerPeerListener(peerListener);
    };

    // Initialize WebRTC
    initializeWebRTC();

    // Cleanup function - only runs on unmount
    return () => {
      if (consumerSessionRef.current) {
        consumerSessionRef.current.close();
        consumerSessionRef.current = null;
      }
      if (webrtcApi.current) {
        webrtcApi.current = null;
      }
    };
  }, [isClient, connectToProducer]); // Minimal dependencies

  return { videoRef, isConnected, isConnecting };
}
