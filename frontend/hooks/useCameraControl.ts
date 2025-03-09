import { useCallback } from "react";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { v4 as uuidv4 } from "uuid";

export function useCameraControl() {
  const { sendMessage } = useWebSocketContext();

  /**
   * Update the active camera
   * @param cameraName The name of the camera to set as active
   */
  const updateCamera = useCallback(
    (cameraName: string) => {
      const messageId = uuidv4();
      sendMessage({
        command: "update_camera",
        camera_name: cameraName,
        message_id: messageId,
      });
      return messageId;
    },
    [sendMessage]
  );

  return {
    updateCamera,
  };
}
