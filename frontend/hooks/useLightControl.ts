import { useCallback } from "react";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { v4 as uuidv4 } from "uuid";

export function useLightControl() {
  const { sendMessage } = useWebSocketContext();

  /**
   * Update a light's properties
   * @param lightName The name of the light to update
   * @param color Optional color value (RGB array or hex string)
   * @param strength Optional light strength/intensity value
   */
  const updateLight = useCallback(
    (lightName: string, color?: string | number[], strength?: number) => {
      const messageId = uuidv4();
      sendMessage({
        command: "update_light",
        light_name: lightName,
        color,
        strength,
        message_id: messageId,
      });
      return messageId;
    },
    [sendMessage]
  );

  return {
    updateLight,
  };
}
