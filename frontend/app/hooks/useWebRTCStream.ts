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

// A consumer session that never produces a track leaves isConnecting latched, which
// then swallows every later producerAdded. Give it a bounded window to deliver.
const CONNECT_TIMEOUT_MS = 15000;
const MAX_CONNECT_ATTEMPTS = 3;
// The RTCPeerConnection is created lazily during negotiation, so we have to poll
// for it — but bounded, not forever.
const PC_POLL_INTERVAL_MS = 100;
const PC_POLL_TIMEOUT_MS = 5000;

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
  const connectTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pcPollTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const connectAttemptsRef = useRef(0);

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

  // Write ref and state together. The refs are read synchronously inside signalling
  // callbacks, which run long before React re-renders and the sync effects above
  // catch up — relying on those alone means a retry can still see the old value.
  const applyConnected = useCallback((value: boolean) => {
    isConnectedRef.current = value;
    setIsConnected(value);
  }, []);

  const applyConnecting = useCallback((value: boolean) => {
    isConnectingRef.current = value;
    setIsConnecting(value);
  }, []);

  const clearPendingTimers = useCallback(() => {
    if (connectTimeoutRef.current) {
      clearTimeout(connectTimeoutRef.current);
      connectTimeoutRef.current = null;
    }
    if (pcPollTimeoutRef.current) {
      clearTimeout(pcPollTimeoutRef.current);
      pcPollTimeoutRef.current = null;
    }
  }, []);

  const teardownSession = useCallback(() => {
    clearPendingTimers();
    if (consumerSessionRef.current) {
      try {
        consumerSessionRef.current.close();
      } catch (error) {
        console.warn("Failed to close consumer session:", error);
      }
      consumerSessionRef.current = null;
    }
  }, [clearPendingTimers]);

  // connectToProducer retries itself via this ref, so the useCallback below can
  // stay free of a self-reference.
  const connectToProducerRef = useRef<(peerId: string) => void>(() => {});

  const connectToProducer = useCallback(
    (peerId: string) => {
      // Check if already connected or connecting using refs
      if (isConnectedRef.current || isConnectingRef.current) {
        return;
      }

      if (!webrtcApi.current) {
        console.error("WebRTC API not available");
        return;
      }

      applyConnecting(true);
      connectAttemptsRef.current += 1;

      const consumerSession = webrtcApi.current.createConsumerSession(peerId);
      consumerSessionRef.current = consumerSession;

      const onStreamReady = () => {
        clearPendingTimers();
        connectAttemptsRef.current = 0;
        applyConnected(true);
        applyConnecting(false);
      };

      // Listen for the primary stream event
      consumerSession.addEventListener("streamsChanged", () => {
        const streams = consumerSession.streams;

        if (videoRef.current && streams && streams.length > 0) {
          videoRef.current.srcObject = streams[0];
          videoRef.current.play().catch(() => {
            // Video play failed - this is often normal due to autoplay policies
          });
          onStreamReady();
          console.info("WebRTC stream connected");
        }
      });

      // Listen for session closure
      consumerSession.addEventListener("closed", () => {
        clearPendingTimers();
        applyConnected(false);
        applyConnecting(false);
      });

      // Listen for errors
      consumerSession.addEventListener("error", (event: any) => {
        console.error("WebRTC consumer session error:", event);
        clearPendingTimers();
        applyConnected(false);
        applyConnecting(false);
      });

      // Also listen to the RTCPeerConnection events directly
      const pcPollDeadline = Date.now() + PC_POLL_TIMEOUT_MS;
      const checkForRTCPeerConnection = () => {
        pcPollTimeoutRef.current = null;

        if (consumerSession.rtcPeerConnection) {
          const pc = consumerSession.rtcPeerConnection;

          pc.addEventListener("track", (event: any) => {
            if (event.streams && event.streams.length > 0 && videoRef.current) {
              videoRef.current.srcObject = event.streams[0];
              onStreamReady();
            }
          });

          pc.addEventListener("connectionstatechange", () => {
            if (
              pc.connectionState === "failed" ||
              pc.connectionState === "disconnected"
            ) {
              clearPendingTimers();
              applyConnected(false);
              applyConnecting(false);
            }
          });
          return;
        }

        // The peer connection is built lazily during negotiation, so poll for it —
        // but give up rather than spinning forever if negotiation never starts.
        if (Date.now() >= pcPollDeadline) {
          console.warn("Gave up waiting for RTCPeerConnection");
          return;
        }
        pcPollTimeoutRef.current = setTimeout(
          checkForRTCPeerConnection,
          PC_POLL_INTERVAL_MS,
        );
      };

      // Start checking for RTCPeerConnection
      pcPollTimeoutRef.current = setTimeout(
        checkForRTCPeerConnection,
        PC_POLL_INTERVAL_MS,
      );

      // Watchdog: a session can sit silently forever if the producer never sends
      // media (it emits no "closed" and no "error"). Without this, isConnecting
      // stays latched and every later producerAdded is ignored.
      connectTimeoutRef.current = setTimeout(() => {
        connectTimeoutRef.current = null;
        if (isConnectedRef.current) return;

        console.warn(
          `WebRTC connect attempt ${connectAttemptsRef.current} timed out after ${CONNECT_TIMEOUT_MS}ms`,
        );
        teardownSession();
        applyConnecting(false);

        if (connectAttemptsRef.current >= MAX_CONNECT_ATTEMPTS) {
          console.error(
            "Giving up on WebRTC stream after " +
              `${MAX_CONNECT_ATTEMPTS} attempts`,
          );
          return;
        }

        // Re-resolve the producer: it may have re-registered under a new peer id.
        const producer = webrtcApi.current
          ?.getAvailableProducers()
          ?.find((p: Peer) => p.meta.name === producerId);
        if (producer) {
          connectToProducerRef.current(producer.id);
        }
        // Otherwise the latch is clear, so a later producerAdded gets through.
      }, CONNECT_TIMEOUT_MS);

      consumerSession.connect();
    },
    [
      producerId,
      clearPendingTimers,
      teardownSession,
      applyConnected,
      applyConnecting,
    ],
  );

  useEffect(() => {
    connectToProducerRef.current = connectToProducer;
  }, [connectToProducer]);

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
          applyConnected(false);
          applyConnecting(false);
        },
      };

      const peerListener: PeerListener = {
        producerAdded: (producer: Peer) => {
          if (producerId && producer.meta.name === producerId) {
            // A fresh registration is a fresh start — don't let a previously
            // exhausted retry budget disable the watchdog for this attempt.
            connectAttemptsRef.current = 0;
            connectToProducer(producer.id);
          }
        },
        producerRemoved: (producer: Peer) => {
          if (producerId && producer.meta.name === producerId) {
            // Drop the dead session, otherwise a producer flap leaks it and the
            // next connect builds a second one alongside.
            teardownSession();
            connectAttemptsRef.current = 0;
            applyConnected(false);
            applyConnecting(false);
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
      teardownSession();
      connectAttemptsRef.current = 0;
      if (webrtcApi.current) {
        webrtcApi.current = null;
      }
    };
  }, [isClient, producerId, connectToProducer, teardownSession]); // Include producerId in dependencies

  return { videoRef, isConnected, isConnecting };
}
