import { createFileRoute } from "@tanstack/react-router";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { PreviewWindow } from "@/components/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { AssetSelection } from "@/components/creative-workspace/AssetSelection";
import { BottomControls } from "@/components/bottom-controls";
import { SceneViewPort } from "@/components/creative-workspace/SceneViewPort";
import { useWebRTCStream } from "@/hooks/useWebRTCStream";

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
    <div className="relative w-full h-screen bg-[#1C1C1C] text-white overflow-hidden">
      <PreviewWindow>
        <SceneViewPort videoRef={videoRef} isConnected={isConnected} />
      </PreviewWindow>

      <ControlsOverlay>
        <SceneControls />

        <AssetSelection />

        <BottomControls />
      </ControlsOverlay>
    </div>
  );
}
