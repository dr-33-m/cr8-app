import { useQuery } from "@tanstack/react-query";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { createSceneObjectsCommand } from "@/websocket/commands/sceneContext";
import { createSceneObjectsQueryOptions } from "@/websocket/query-manager/scene-context";

export function useSceneContext() {
  const { socket, isFullyConnected } = useWebSocketContext();

  // Create command with current socket
  const commandFn = createSceneObjectsCommand(socket);

  const { data, isLoading, error, refetch } = useQuery({
    ...createSceneObjectsQueryOptions(commandFn),
    enabled: isFullyConnected, // Only query when connected
  });

  return {
    objects: data?.objects ?? [],
    timestamp: data?.timestamp ?? 0,
    loading: isLoading,
    error: error?.message,
    refresh: refetch,
    // Helper methods (computed from data)
    getObjectByName: (name: string) =>
      data?.objects.find((obj) => obj.name === name),
    getObjectsByType: (type: string) =>
      data?.objects.filter((obj) => obj.type === type),
  };
}
