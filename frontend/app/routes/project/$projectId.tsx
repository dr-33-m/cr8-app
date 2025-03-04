import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState, useCallback } from "react";
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
import { useSceneConfigStore } from "@/store/sceneConfiguratorStore";
import { useProjectStore } from "@/store/projectStore";
import { toast } from "sonner";
import { useNavigate } from "@tanstack/react-router";
import { useServerHealth } from "@/hooks/useServerHealth";

export const Route = createFileRoute("/project/$projectId")({
  component: RouteComponent,
});

function RouteComponent() {
  const [blender_connected, setBlenderConnected] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { serverStatus } = useServerHealth();
  const navigate = useNavigate();

  const {
    sceneConfiguration,
    updateSceneConfiguration,
    removeSceneConfiguration,
    resetSceneConfiguration,
  } = useSceneConfigStore();

  const { name: projectName, template, clearProject } = useProjectStore();
  const { clearControls } = useTemplateControlsStore();

  // Redirect if no project data is available
  useEffect(() => {
    if (!projectName || !template || serverStatus !== "healthy") {
      toast.error("No project data found");
      navigate({ to: "/" });
      return;
    }
  }, [projectName, template, navigate, serverStatus]);

  // Cleanup project data when leaving
  useEffect(() => {
    return () => {
      clearProject();
      clearControls();
    };
  }, [clearProject]);

  const updateCanvas = useCallback((imageData: string) => {
    if (!canvasRef.current) {
      console.error("Canvas ref is not attached");
      return;
    }

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    if (!ctx) {
      console.error("Unable to get 2D rendering context");
      return;
    }

    const img = new Image();
    img.onload = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
    img.src = `data:image/png;base64,${imageData}`;
  }, []);

  const { websocket, isConnected, requestTemplateControls } =
    useWebSocketContext();

  const {
    isLoading,
    isPlaying,
    isPreviewAvailable,
    shootPreview,
    playbackPreview,
    stopPlaybackPreview,
    generateVideo,
  } = usePreviewRenderer(websocket, {
    onMessage: useCallback(
      (data: any) => {
        try {
          if (data.type === "frame") {
            updateCanvas(data.data);
          } else if (data.command === "template_controls") {
            const setTemplateControls =
              useTemplateControlsStore.getState().setControls;
            setTemplateControls(data.controllables);
            toast.success("Template controls loaded");
          } else if (
            data.type === "system" &&
            data.status === "blender_connected"
          ) {
            setBlenderConnected(true);
          }
          // Handle asset operation responses
          else if (data.command === "append_asset_result") {
            if (data.status === "success") {
              toast.success("Asset placed successfully");
            } else {
              toast.error(
                `Failed to place asset: ${data.data?.message || "Unknown error"}`
              );
              // Could revert optimistic update here if needed
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
      },
      [updateCanvas]
    ),
  });

  // Request template controls when connected
  useEffect(() => {
    if (blender_connected || isConnected) {
      requestTemplateControls();
    }
  }, [isConnected, requestTemplateControls, blender_connected]);

  // Set up canvas dimensions
  useEffect(() => {
    if (canvasRef.current) {
      canvasRef.current.width = 800;
      canvasRef.current.height = 600;
    }
  }, []);

  return (
    <div className="relative w-full h-screen bg-[#1C1C1C] text-white">
      <PreviewWindow>
        <SceneViewPort
          canvasRef={canvasRef}
          isPreviewAvailable={isPreviewAvailable}
          finalVideoUrl=""
        />
      </PreviewWindow>

      <ControlsOverlay>
        <SceneControls
          sceneConfiguration={sceneConfiguration}
          onUpdateSceneConfiguration={updateSceneConfiguration}
        />

        <AssetSelection />

        <BottomControls>
          <SceneActions
            onShootPreview={() =>
              shootPreview(sceneConfiguration, resetSceneConfiguration)
            }
            onPlaybackPreview={playbackPreview}
            onStopPlaybackPreview={stopPlaybackPreview}
            onGenerateVideo={generateVideo}
            assets={sceneConfiguration}
            onRemoveAsset={removeSceneConfiguration}
            isLoading={isLoading}
            isPlaying={isPlaying}
            isFinalVideoReady={false}
          />
        </BottomControls>
      </ControlsOverlay>
    </div>
  );
}
