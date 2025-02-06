import { useEffect, useRef, useState, useCallback } from "react";
import { useProjectStore } from "@/store/projectStore";
import useUserStore from "@/store/userStore";
import { toast } from "sonner";
import { WebSocketStatus, WebSocketMessage } from "@/lib/types/websocket";

const INITIAL_RECONNECT_DELAY = 1000;
const MAX_RECONNECT_DELAY = 30000;
const MAX_RECONNECT_ATTEMPTS = 5;

export const useWebSocket = (onMessage?: (data: any) => void) => {
  const [status, setStatus] = useState<WebSocketStatus>("disconnected");
  const [reconnectAttempts, setReconnectAttempts] = useState(0);
  const websocketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const onMessageCallback = useRef(onMessage);
  const isManuallyDisconnected = useRef(false);
  const messageQueueRef = useRef<WebSocketMessage[]>([]);

  const userInfo = useUserStore((store) => store.userInfo);
  const { template } = useProjectStore();
  const websocketUrl = import.meta.env.VITE_WEBSOCKET_URL;

  // Update callback ref when onMessage changes
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
      INITIAL_RECONNECT_DELAY * Math.pow(2, reconnectAttempts),
      MAX_RECONNECT_DELAY
    );
  }, [reconnectAttempts]);

  const sendMessage = useCallback((message: WebSocketMessage) => {
    if (websocketRef.current?.readyState === WebSocket.OPEN) {
      websocketRef.current.send(JSON.stringify(message));
    } else {
      messageQueueRef.current.push(message);
      toast.info("Message queued - waiting for connection");
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (websocketRef.current) {
      isManuallyDisconnected.current = true;
      websocketRef.current.close();
      websocketRef.current = null;
    }
    setStatus("disconnected");
    setReconnectAttempts(0);
  }, []);

  const connect = useCallback(() => {
    const url = getWebSocketUrl();
    if (!url) {
      toast.error("Missing connection details");
      return;
    }

    // Reset manual disconnect flag
    isManuallyDisconnected.current = false;

    try {
      setStatus("connecting");
      const ws = new WebSocket(url);
      websocketRef.current = ws;

      ws.onopen = () => {
        setStatus("connected");
        setReconnectAttempts(0);
        toast.success("Connected to server");

        // Send any queued messages
        while (messageQueueRef.current.length > 0) {
          const message = messageQueueRef.current.shift();
          if (message) sendMessage(message);
        }
      };

      ws.onclose = () => {
        setStatus("disconnected");
        websocketRef.current = null;

        // Don't attempt to reconnect if manually disconnected
        if (isManuallyDisconnected.current) {
          return;
        }

        // Attempt to reconnect if we haven't exceeded max attempts
        if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
          const delay = calculateReconnectDelay();
          toast.info(
            `Connection lost. Reconnecting in ${delay / 1000} seconds...`
          );

          reconnectTimeoutRef.current = setTimeout(() => {
            setReconnectAttempts((prev) => prev + 1);
            connect();
          }, delay);
        } else {
          toast.error(
            "Unable to establish connection. Please check your connection and try again."
          );
        }
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
        toast.error("Connection error occurred");
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
    }
  }, [
    getWebSocketUrl,
    calculateReconnectDelay,
    reconnectAttempts,
    sendMessage,
  ]);

  const reconnect = useCallback(() => {
    disconnect();
    connect();
  }, [disconnect, connect]);

  const requestTemplateControls = useCallback(() => {
    sendMessage({ command: "get_template_controls" });
  }, [sendMessage]);

  // Initial connection
  useEffect(() => {
    if (userInfo?.username && template) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [connect, disconnect, userInfo?.username, template]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (
        document.visibilityState === "visible" &&
        status === "disconnected" &&
        !isManuallyDisconnected.current
      ) {
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
