import { useEffect } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { PreviewWindow } from "@/components/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { BottomControls } from "@/components/bottom-controls";
import { SavingOverlay } from "@/components/SavingOverlay";
import { ExitWorkspace } from "@/components/creative-workspace/ExitWorkspace";
import { SceneViewPort } from "@/components/creative-workspace/SceneViewPort";
import { useWebRTCStream } from "@/hooks/useWebRTCStream";
import { AssetBrowser } from "@/components/creative-workspace/asset-browser/AssetBrowser";
import useUserStore from "@/store/userStore";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { sceneContextKeys } from "@/websocket/query-manager/scene-context";

const isRemoteMode = import.meta.env.VITE_LAUNCH_MODE === "remote";

export const Route = createFileRoute("/workspace/")({
  component: RouteComponent,
});

function RouteComponent() {
  const { auth } = Route.useRouteContext();
  const remoteUser =
    isRemoteMode && auth.isAuthenticated ? auth.user.name : undefined;

  return (
    <WebSocketProvider remoteUser={remoteUser}>
      <WorkspaceContent remoteUser={remoteUser} />
    </WebSocketProvider>
  );
}

function WorkspaceContent({ remoteUser }: { remoteUser?: string }) {
  const storeUsername = useUserStore((state) => state.username);
  const username = (remoteUser || storeUsername)?.split(" ")[0];
  const producerId = username ? `blender-${username}` : null;
  const { videoRef, isConnected } = useWebRTCStream(producerId);
  const { instanceStatus, cancelLaunch, reconnect, blenderConnectedOnce } =
    useWebSocketContext();
  const queryClient = useQueryClient();

  // Entering the workspace fresh — drop any scene objects cached from a previous
  // workspace so the new one doesn't briefly show the wrong scene.
  useEffect(() => {
    queryClient.setQueryData(sceneContextKeys.objects(), null);
  }, [queryClient]);

  // Only surface the stream once THIS workspace's Blender has connected — before
  // that, a switch could briefly show the previous instance's feed. Uses the
  // "connected once" latch so a later reconnect blip doesn't hide a live stream.
  const streamReady = isConnected && blenderConnectedOnce;

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <PreviewWindow>
        <SceneViewPort
          videoRef={videoRef}
          isConnected={streamReady}
          instanceStatus={instanceStatus}
          cancelLaunch={cancelLaunch}
          onRetry={reconnect}
        />
      </PreviewWindow>

      <ControlsOverlay>
        <SceneControls />

        <AssetBrowser />

        <BottomControls />
      </ControlsOverlay>

      <ExitWorkspace />

      <SavingOverlay />
    </div>
  );
}
