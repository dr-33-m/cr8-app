import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useCallback } from "react";
import { WebSocketProvider } from "@/contexts/WebSocketContext";
import { PreviewWindow } from "@/components/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { AssetSelection } from "@/components/creative-workspace/AssetSelection";
import { BottomControls } from "@/components/BottomControls";
import { SceneViewPort } from "@/components/creative-workspace/SceneViewPort";
import { SceneActions } from "@/components/creative-workspace/SceneActions";
import { useTemplateControlsStore } from "@/store/TemplateControlsStore";
import { usePreviewRenderer } from "@/hooks/usePreviewRenderer";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { useAnimationStore } from "@/store/animationStore";
import { useAssetPlacerStore } from "@/store/assetPlacerStore";
import { useWebRTCStream } from "@/hooks/useWebRTCStream";
import { toast } from "sonner";

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
  const { clearControls } = useTemplateControlsStore();
  const { videoRef, isConnected } = useWebRTCStream();

  // Cleanup project data when leaving
  useEffect(() => {
    return () => {
      clearControls();
      useAssetPlacerStore.getState().clearPlacedAssets();
      useAnimationStore.getState().clearSelections();
    };
  }, [clearControls]);

  const { websocket, isFullyConnected, requestTemplateControls } =
    useWebSocketContext();

  const { generateVideo } = usePreviewRenderer(websocket, {
    onMessage: useCallback((data: any) => {
      try {
        // Handle asset operation responses
        if (data.command === "append_asset_result") {
          if (data.status === "success") {
            toast.success("Asset placed successfully");
          } else {
            toast.error(
              `Failed to place asset: ${data.data?.message || "Unknown error"}`
            );
          }
        } else if (data.command === "remove_assets_result") {
          if (data.status === "success") {
            toast.success("Asset removed successfully");
          } else {
            toast.error(
              `Failed to remove asset: ${data.data?.message || "Unknown error"}`
            );
          }
        } else if (data.command === "rotate_assets_result") {
          if (data.status === "success") {
            toast.success("Asset rotated successfully");
          } else {
            toast.error(
              `Failed to rotate asset: ${data.data?.message || "Unknown error"}`
            );
          }
        } else if (data.command === "scale_assets_result") {
          if (data.status === "success") {
            toast.success("Asset scaled successfully");
          } else {
            toast.error(
              `Failed to scale asset: ${data.data?.message || "Unknown error"}`
            );
          }
        }
      } catch (error) {
        console.error("Error handling WebSocket message:", error);
        toast.error("Failed to process server message");
      }
    }, []),
  });

  // Track if animations have been loaded
  const animationsLoaded = useRef(false);

  // Request template controls and animations when connected
  useEffect(() => {
    if (isFullyConnected) {
      // Request template controls
      requestTemplateControls();

      // Load animations if not already loaded
      if (!animationsLoaded.current) {
        animationsLoaded.current = true;
        const fetchAnimations = useAnimationStore.getState().fetchAllAnimations;
        fetchAnimations();
      }
    }
  }, [isFullyConnected, requestTemplateControls]);

  return (
    <div className="relative w-full h-screen bg-[#1C1C1C] text-white">
      <PreviewWindow>
        <SceneViewPort
          videoRef={videoRef}
          isConnected={isConnected}
          finalVideoUrl=""
        />
      </PreviewWindow>

      <ControlsOverlay>
        <SceneControls />

        <AssetSelection />

        <BottomControls>
          <SceneActions
            onGenerateVideo={generateVideo}
            isFinalVideoReady={false}
          />
        </BottomControls>
      </ControlsOverlay>
    </div>
  );
}
