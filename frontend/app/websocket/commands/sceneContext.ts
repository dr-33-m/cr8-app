import { Socket } from "socket.io-client";
import { SceneObject } from "@/lib/types/stores";

export interface SceneObjectsResponse {
  objects: SceneObject[];
  timestamp: number;
}

export function createSceneObjectsCommand(socket: Socket | null) {
  return (): Promise<SceneObjectsResponse> => {
    if (!socket?.connected) {
      return Promise.reject(new Error("WebSocket not connected"));
    }

    return new Promise((resolve, reject) => {
      const messageId = `scene_objects_query_${Date.now()}`;
      const timeout = setTimeout(() => {
        socket.off(`response_${messageId}`);
        reject(new Error("Query timeout after 5s"));
      }, 5000);

      // Listen for this specific response
      socket.once(`response_${messageId}`, (response: any) => {
        clearTimeout(timeout);

        if (response.status === "success" && response.data?.data) {
          resolve({
            objects: response.data.data,
            timestamp: Math.floor(Date.now() / 1000),
          });
        } else {
          reject(new Error(response.error?.user_message || "Query failed"));
        }
      });

      // Send query
      socket.emit("command_sent", {
        message_id: messageId,
        type: "command_sent",
        payload: {
          addon_id: "multi_registry_assets",
          command: "list_scene_objects",
          params: {},
        },
        metadata: {
          route: "direct",
          source: "browser",
        },
      });
    });
  };
}
