import { createFileRoute } from "@tanstack/react-router";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { PreviewWindow } from "@/components/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { BottomControls } from "@/components/bottom-controls";
import { SceneViewPort } from "@/components/creative-workspace/SceneViewPort";
import { useWebRTCStream } from "@/hooks/useWebRTCStream";
import { AssetBrowser } from "@/components/creative-workspace/asset-browser/AssetBrowser";

export const Route = createFileRoute("/workspace/")({
  component: RouteComponent,
});

function RouteComponent() {
  return (
    <WebSocketProvider>
      <WorkspaceContent />
    </WebSocketProvider>
  );
}

function WorkspaceContent() {
  const { videoRef, isConnected } = useWebRTCStream();

  return (
    <div className="relative w-full h-screen overflow-hidden">
      <PreviewWindow>
        <SceneViewPort videoRef={videoRef} isConnected={isConnected} />
      </PreviewWindow>

      <ControlsOverlay>
        <SceneControls />

        <AssetBrowser />

        <BottomControls />
      </ControlsOverlay>
    </div>
  );
}
