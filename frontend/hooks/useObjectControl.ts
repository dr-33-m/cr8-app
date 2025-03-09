import { useCallback } from "react";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { v4 as uuidv4 } from "uuid";

export function useObjectControl() {
  const { sendMessage } = useWebSocketContext();

  /**
   * Update an object's transform properties
   * @param objectName The name of the object to update
   * @param location Optional location/position (XYZ array)
   * @param rotation Optional rotation (XYZ array in degrees or radians)
   * @param scale Optional scale (XYZ array or uniform scale)
   */
  const updateObject = useCallback(
    (
      objectName: string,
      location?: number[],
      rotation?: number[],
      scale?: number[]
    ) => {
      const messageId = uuidv4();
      sendMessage({
        command: "update_object",
        object_name: objectName,
        location,
        rotation,
        scale,
        message_id: messageId,
      });
      return messageId;
    },
    [sendMessage]
  );

  return {
    updateObject,
  };
}
