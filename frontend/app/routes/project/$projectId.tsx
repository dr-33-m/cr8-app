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

export const Route = createFileRoute("/project/$projectId")({
  component: RouteComponent,
});

function RouteComponent() {
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const navigate = useNavigate();

  const {
    sceneConfiguration,
    updateSceneConfiguration,
    removeSceneConfiguration,
  } = useSceneConfigStore();

  const { name: projectName, template, clearProject } = useProjectStore();
  const { clearControls } = useTemplateControlsStore();

  // Redirect if no project data is available
  useEffect(() => {
    if (!projectName || !template) {
      toast.error("No project data found");
      navigate({ to: "/" });
      return;
    }
  }, [projectName, template, navigate]);

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
    setIsPreviewAvailable,
    setIsLoading,
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
    if (isConnected) {
      requestTemplateControls();
    }
  }, [isConnected, requestTemplateControls]);

  // Set up canvas dimensions
  useEffect(() => {
    if (canvasRef.current) {
      canvasRef.current.width = 800; // Set your desired width
      canvasRef.current.height = 600; // Set your desired height
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

        <AssetSelection
          selectedAsset={selectedAsset}
          onSelectAsset={setSelectedAsset}
        />

        <BottomControls>
          <SceneActions
            onShootPreview={() => shootPreview(sceneConfiguration)}
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
