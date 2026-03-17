import { useEffect, useRef, useState, useCallback } from "react";

const SIGNALLING_SERVER_URL = import.meta.env.VITE_WEBRTC_SIGNALING_SERVER_URL;
const TURN_SERVER_URL = import.meta.env.VITE_TURN_SERVER;

import { ConnectionListener, PeerListener, Peer } from "@/lib/types/websocket";

/**
 * Parse a TURN URL (turn://username:password@host:port) into RTCIceServer format.
 * The password in the TURN URL is already URL-encoded, so we decode it for the browser.
 */
function parseTurnUrl(turnUrl: string): RTCIceServer | null {
  try {
    const parsed = new URL(turnUrl);
    if (parsed.protocol !== "turn:") {
      console.warn("Non-TURN URL provided, skipping:", parsed.protocol);
      return null;
    }

    return {
      urls: `turn:${parsed.hostname}:${parsed.port}`,
      username: parsed.username,
      credential: decodeURIComponent(parsed.password),
    };
  } catch (error) {
    console.error("Failed to parse TURN URL:", error);
    return null;
  }
}

/**
 * Build ICE servers config for WebRTC, including STUN and optional TURN.
 */
function buildIceServers(): RTCIceServer[] {
  const iceServers: RTCIceServer[] = [
    // Google's public STUN server - free and reliable for direct UDP connections
    { urls: "stun:stun.l.google.com:19302" },
    { urls: "stun:stun1.l.google.com:19302" },
  ];

  // Add TURN server if configured - needed for NAT traversal on VastAI
  if (TURN_SERVER_URL) {
    const turnServer = parseTurnUrl(TURN_SERVER_URL);
    if (turnServer) {
      iceServers.push(turnServer);
      console.info("TURN server configured for ICE relay");
    }
  }

  return iceServers;
}

export function useWebRTCStream(producerId: string | null) {
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

      const iceServers = buildIceServers();
      console.info(
        "Initializing WebRTC with ICE servers:",
        iceServers.map((s) => s.urls),
      );

      webrtcApi.current = new GstWebRTCAPIRef.current({
        meta: {},
        signalingServerUrl: SIGNALLING_SERVER_URL,
        reconnectionTimeout: 5000,
        webrtcConfig: { iceServers },
      });

      const connectionListener: ConnectionListener = {
        connected: (clientId: string) => {
          console.info("Connected to WebRTC signaling server");

          if (webrtcApi.current && producerId) {
            const producers = webrtcApi.current.getAvailableProducers();
            const producer = producers.find(
              (p: Peer) => p.meta.name === producerId,
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
          if (producerId && producer.meta.name === producerId) {
            connectToProducer(producer.id);
          }
        },
        producerRemoved: (producer: Peer) => {
          if (producerId && producer.meta.name === producerId) {
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
  }, [isClient, producerId, connectToProducer]); // Include producerId in dependencies

  return { videoRef, isConnected, isConnecting };
}
