import { useCallback } from "react";
import { useWebSocket } from "./useWebsocket";
import { v4 as uuidv4 } from "uuid";

export function useMaterialControl() {
  const { sendMessage } = useWebSocket();

  /**
   * Update a material's properties
   * @param materialName The name of the material to update
   * @param color Optional color value (RGB array or hex string)
   * @param roughness Optional roughness value (0-1)
   * @param metallic Optional metallic value (0-1)
   */
  const updateMaterial = useCallback(
    (
      materialName: string,
      color?: string | number[],
      roughness?: number,
      metallic?: number
    ) => {
      const messageId = uuidv4();
      sendMessage({
        command: "update_material",
        material_name: materialName,
        color,
        roughness,
        metallic,
        message_id: messageId,
      });
      return messageId;
    },
    [sendMessage]
  );

  return {
    updateMaterial,
  };
}
