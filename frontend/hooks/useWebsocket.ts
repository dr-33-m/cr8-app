import { useEffect, useRef, useState, useCallback } from "react";
import { useProjectStore } from "@/store/projectStore";
import useUserStore from "@/store/userStore";
import { toast } from "sonner";
import { WebSocketMessage, WebSocketStatus } from "@/lib/types/websocket";

const MAX_RECONNECT_DELAY = 30000;
const MAX_RECONNECT_ATTEMPTS = 5;
const BASE_DELAY = 2000;

export const useWebSocket = (onMessage?: (data: any) => void) => {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const reconnectAttemptsRef = useRef(0);
  const onMessageCallback = useRef(onMessage);
  const isManuallyDisconnected = useRef(false);
  const messageQueueRef = useRef<WebSocketMessage[]>([]);

  const userInfo = useUserStore((store) => store.userInfo);
  const { template } = useProjectStore();
  const websocketUrl = import.meta.env.VITE_WEBSOCKET_URL;

  useEffect(() => {
    onMessageCallback.current = onMessage;
  }, [onMessage]);

  const getWebSocketUrl = useCallback(() => {
    if (!userInfo?.username || !template) {
      return null;
    }
    return `${websocketUrl}/${userInfo.username}/browser?blend_file=${template}`;
  }, [userInfo?.username, template, websocketUrl]);

  const calculateReconnectDelay = useCallback(() => {
    return Math.min(
      BASE_DELAY * Math.pow(2, reconnectAttemptsRef.current),
      MAX_RECONNECT_DELAY
    );
  }, []);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message));
    } else {
      messageQueueRef.current.push(message);
      toast.info("Message queued - waiting for connection");
    }
  }, []);

  const disconnect = useCallback(() => {
    // Clear any pending reconnection attempts
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = undefined;
    }

    // Close existing connection if any
    if (websocketRef.current) {
      isManuallyDisconnected.current = true;
      websocketRef.current.close();
      websocketRef.current = null;
    }

    // Reset all state
    setStatus("disconnected");
    reconnectAttemptsRef.current = 0;
    messageQueueRef.current = [];
    isManuallyDisconnected.current = true;
  }, []);

  const attemptReconnect = useCallback(() => {
    if (isManuallyDisconnected.current) {
      return false;
    }

    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      setStatus("failed");
      toast.error(
        "Maximum reconnection attempts reached. Please refresh the page to try again."
      );
      return false;
    }

    const delay = calculateReconnectDelay();
    toast.info(`Attempting to reconnect in ${delay / 1000} seconds...`);

    // Clear any existing timeout
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    reconnectTimeoutRef.current = setTimeout(() => {
      reconnectAttemptsRef.current += 1;
      connect();
    }, delay);

    return true;
  }, [calculateReconnectDelay]);

  const connect = useCallback(() => {
    const url = getWebSocketUrl();
    if (!url) {
      toast.error("Missing connection details");
      return;
    }

    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      setStatus("failed");
      toast.error(
        "Maximum reconnection attempts reached. Please refresh the page to try again."
      );
      return;
    }

    isManuallyDisconnected.current = false;

    try {
      setStatus("connecting");
      const ws = new WebSocket(url);
      websocketRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        reconnectAttemptsRef.current = 0;
        isManuallyDisconnected.current = false;
        toast.success("Connected to server");

        while (messageQueueRef.current.length > 0) {
          const message = messageQueueRef.current.shift();
          if (message) sendMessage(message);
        }
      };

      ws.onclose = (event) => {
        websocketRef.current = null;

        if (isManuallyDisconnected.current) {
          setStatus("disconnected");
          return;
        }

        if (event.code === 1000 || event.code === 1001) {
          setStatus("disconnected");
          return;
        }

        setStatus("disconnected");
        attemptReconnect();
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        toast.error("Connection error occurred");
        // Don't increment reconnectAttempts here, let onclose handle it
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (onMessageCallback.current) {
            onMessageCallback.current(data);
          }
        } catch (error) {
          console.error("Error parsing WebSocket message:", error);
          toast.error("Failed to process server message");
        }
      };
    } catch (error) {
      console.error("Error creating WebSocket:", error);
      setStatus("disconnected");
      toast.error("Failed to establish connection");
      attemptReconnect();
    }
  }, [getWebSocketUrl, sendMessage, attemptReconnect]);

  const reconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= MAX_RECONNECT_ATTEMPTS) {
      toast.error(
        "Maximum reconnection attempts reached. Please refresh the page to try again."
      );
      return;
    }
    isManuallyDisconnected.current = false;
    disconnect();
    connect();
  }, [disconnect, connect]);

  const requestTemplateControls = useCallback(() => {
    sendMessage({ command: "get_template_controls" });
  }, [sendMessage]);

  useEffect(() => {
    if (userInfo?.username && template) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [connect, disconnect, userInfo?.username, template]);

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (
        document.visibilityState === "visible" &&
        status === "disconnected" &&
        !isManuallyDisconnected.current &&
        reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS
      ) {
        // Reset reconnect attempts when manually trying to reconnect
        reconnectAttemptsRef.current = 0;
        reconnect();
      }
    };

    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [status, reconnect]);

  return {
    status,
    websocket: websocketRef.current,
    isConnected: status === "connected",
    reconnect,
    disconnect,
    sendMessage,
    requestTemplateControls,
  };
};
