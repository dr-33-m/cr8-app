import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { PreviewWindow } from "@/components/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { AssetSelection } from "@/components/creative-workspace/AssetSelection";
import { BottomControls } from "@/components/BottomControls";
import { SceneViewPort } from "@/components/creative-workspace/SceneViewPort";
import { SceneActions } from "@/components/creative-workspace/SceneActions";
import { useTemplateControlsStore } from "@/store/TemplateControlsStore";
import { usePreviewRenderer } from "@/hooks/usePreviewRenderer";
import { useWebSocket } from "@/hooks/useWebsocket";
import { useSceneConfigStore } from "@/store/sceneConfiguratorStore";

export const Route = createFileRoute("/project/$projectId")({
  component: RouteComponent,
});

function RouteComponent() {
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { websocket, isConnected, requestTemplateControls } = useWebSocket();
  const {
    sceneConfiguration,
    updateSceneConfiguration,
    removeSceneConfiguration,
  } = useSceneConfigStore();
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
  } = usePreviewRenderer(websocket);

  const updateCanvas = (imageData: string) => {
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
  };

  useEffect(() => {
    if (isConnected) {
      requestTemplateControls();
    }
  }, [isConnected, requestTemplateControls]);

  if (isConnected && websocket) {
    websocket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === "frame") {
          updateCanvas(data.data);
          setIsPreviewAvailable(true);
          setIsLoading(false);
        } else if (data.type === "viewport_stream_error") {
          console.error("Viewport stream error:", data.message);
          setIsLoading(false);
        } else if (data.command === "template_controls") {
          const setTemplateControls =
            useTemplateControlsStore.getState().setControls;
          setTemplateControls(data.controllables);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
        setIsLoading(false);
      }
    };
  }

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
