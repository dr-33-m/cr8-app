import { UseQueryOptions } from "@tanstack/react-query";
import { SceneObjectsResponse } from "@/websocket/commands/sceneContext";
import { sceneContextKeys } from "./keys";

export function createSceneObjectsQueryOptions(
  commandFn: () => Promise<SceneObjectsResponse>,
  options?: Partial<UseQueryOptions<SceneObjectsResponse>>
) {
  return {
    queryKey: sceneContextKeys.objects(),
    queryFn: commandFn,
    staleTime: 0, // Always stale (real-time data)
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 2000, // Poll every 2 seconds
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: true,
    refetchOnReconnect: true,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    ...options,
  } satisfies UseQueryOptions<SceneObjectsResponse>;
}
