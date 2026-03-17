import { Socket } from "socket.io-client";
import { SceneObject } from "@/lib/types/stores";

export interface SceneObjectsResponse {
  objects: SceneObject[];
  timestamp: number;
}

// In-flight guard — only one list_scene_objects query at a time.
// Prevents overlapping requests from stacking up when TanStack Query fires
// multiple simultaneous refetches (focus, reconnect, polling overlap).
let inFlight = false;

export function createSceneObjectsCommand(socket: Socket | null) {
  return (): Promise<SceneObjectsResponse> => {
    if (!socket?.connected) {
      return Promise.reject(new Error("WebSocket not connected"));
    }

    if (inFlight) {
      return Promise.reject(new Error("Scene query already in flight"));
    }

    inFlight = true;

    return new Promise((resolve, reject) => {
      const messageId = `scene_objects_query_${Date.now()}`;
      const timeout = setTimeout(() => {
        inFlight = false;
        socket.off(`response_${messageId}`);
        reject(new Error("Query timeout after 5s"));
      }, 5000);

      // Listen for this specific response
      socket.once(`response_${messageId}`, (response: any) => {
        clearTimeout(timeout);
        inFlight = false;

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
