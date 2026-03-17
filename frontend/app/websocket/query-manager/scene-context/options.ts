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
    staleTime: 3000, // Don't refetch if data is < 3s old (prevents focus/reconnect spikes)
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: 5000, // Poll every 5 seconds — sufficient for passive scene sync
    refetchIntervalInBackground: true,
    refetchOnWindowFocus: false, // Polling covers it; focus events cause burst traffic
    refetchOnReconnect: true,
    retry: 1, // One retry is enough — fewer retries reduces pile-up on failure
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    ...options,
  } satisfies UseQueryOptions<SceneObjectsResponse>;
}
