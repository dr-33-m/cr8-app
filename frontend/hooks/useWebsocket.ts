import { useProjectStore } from "@/store/projectStore";
import useUserStore from "@/store/userStore";
import { useEffect, useRef, useState, useCallback } from "react";

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const websocketRef = useRef<WebSocket | null>(null);
  const userInfo = useUserStore((store) => store.userInfo);
  const { template } = useProjectStore();
  const blend_file = template;

  console.log(blend_file, "blend file");
  useEffect(() => {
    if (!userInfo?.username || !blend_file) return;

    const connectWebSocket = () => {
      const ws = new WebSocket(
        `ws://localhost:8000/ws/${userInfo?.username}/browser?blend_file=${blend_file}`
      );
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log("WebSocket connection established");
        setIsConnected(true);
        ws.send(JSON.stringify({ status: "Connected" }));
      };

      ws.onclose = () => {
        console.log("WebSocket connection closed");
        setIsConnected(false);
        // Try to reconnect after a short delay
        setTimeout(connectWebSocket, 1000);
      };

      ws.onerror = (error) => {
        console.error("WebSocket error:", error);
      };
    };

    connectWebSocket();

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, [userInfo?.username, blend_file]);

  const requestTemplateControls = useCallback(() => {
    if (
      websocketRef.current &&
      websocketRef.current.readyState === WebSocket.OPEN
    ) {
      websocketRef.current.send(
        JSON.stringify({ command: "get_template_controls" })
      );
    }
  }, []);

  return {
    websocket: websocketRef.current,
    isConnected,
    requestTemplateControls,
  };
};
