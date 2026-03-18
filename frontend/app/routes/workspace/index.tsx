import { createFileRoute } from "@tanstack/react-router";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { PreviewWindow } from "@/components/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { BottomControls } from "@/components/bottom-controls";
import { SceneViewPort } from "@/components/creative-workspace/SceneViewPort";
import { useWebRTCStream } from "@/hooks/useWebRTCStream";
import { AssetBrowser } from "@/components/creative-workspace/asset-browser/AssetBrowser";
import useUserStore from "@/store/userStore";
import { useWebSocketContext } from "@/contexts/WebSocketContext";

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
  const username = remoteUser || storeUsername;
  const producerId = username ? `blender-${username}` : null;
  const { videoRef, isConnected } = useWebRTCStream(producerId);
  const { instanceStatus, cancelLaunch, reconnect } = useWebSocketContext();

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <PreviewWindow>
        <SceneViewPort
          videoRef={videoRef}
          isConnected={isConnected}
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
    </div>
  );
}
