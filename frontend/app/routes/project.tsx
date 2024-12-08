import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { PreviewWindow } from "@/components/creative-workspace/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { AssetSelection } from "@/components/creative-workspace/AssetSelection";
import { BottomControls } from "@/components/creative-workspace/BottomControls";
import { SceneConfiguration } from "@/lib/types/sceneConfig";

export const Route = createFileRoute("/project")({
  component: RouteComponent,
});

function RouteComponent() {
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null);
  const [isSceneControlsVisible, setIsSceneControlsVisible] =
    useState<boolean>(true);
  const [isAssetSelectionVisible, setIsAssetSelectionVisible] =
    useState<boolean>(true);
  const [isBottomControlsVisible, setIsBottomControlsVisible] =
    useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  // const [viewportImage, setViewportImage] = useState<string | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const [sceneConfiguration, setSceneConfiguration] =
    useState<SceneConfiguration>({});

  const toggleFullscreen = () => {
    setIsFullscreen((prev) => {
      const newState = !prev;
      // Update other state values based on the fullscreen state
      setIsSceneControlsVisible(!newState);
      setIsAssetSelectionVisible(!newState);
      setIsBottomControlsVisible(!newState);

      return newState;
    });
  };
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPreviewAvailable, setIsPreviewAvailable] = useState<boolean>(false);

  useEffect(() => {
    // Establish WebSocket connection
    const ws = new WebSocket("ws://localhost:5001/browser");
    websocketRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection established");
      // Send initialization message
      ws.send(JSON.stringify({ action: "initialize" }));
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle viewport stream
        if (data.type === "frame") {
          updateCanvas(data.data);
          setIsPreviewAvailable(true);
        } else if (data.type === "viewport_stream_error") {
          console.error("Viewport stream error:", data.message);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };

    // Cleanup on component unmount
    return () => {
      if (ws) {
        ws.close();
      }
    };
  }, []);

  const updateCanvas = (imageData) => {
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

  const shootPreview = () => {
    if (
      websocketRef.current &&
      websocketRef.current.readyState === WebSocket.OPEN
    ) {
      websocketRef.current.send(
        JSON.stringify({
          command: "start_preview_rendering",
          params: {
            resolution_x: 1280,
            resolution_y: 720,
            samples: 16,
            num_frames: 80,
            subcommands: sceneConfiguration,
          },
        })
      );
    } else {
      console.error("WebSocket is not open");
    }
  };
  const playbackPreview = () => {
    if (
      websocketRef.current &&
      websocketRef.current.readyState === WebSocket.OPEN
    ) {
      websocketRef.current.send(
        JSON.stringify({
          command: "start_broadcast",
        })
      );
    } else {
      console.error("WebSocket is not open");
    }
  };

  const updateSceneConfiguration = (
    key: keyof SceneConfiguration,
    value: any
  ) => {
    setSceneConfiguration((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const removeSceneConfiguration = (key: keyof SceneConfiguration) => {
    setSceneConfiguration((prev) => {
      const { [key]: _, ...rest } = prev;
      return rest;
    });
  };

  return (
    <div className="relative w-full h-screen bg-[#1C1C1C] text-white overflow-hidden">
      <PreviewWindow
        isFullscreen={isFullscreen}
        canvasRef={canvasRef}
        isPreviewAvailable={isPreviewAvailable}
      />

      <ControlsOverlay
        isFullscreen={isFullscreen}
        toggleFullscreen={toggleFullscreen}
      >
        <SceneControls
          isVisible={isSceneControlsVisible}
          onToggleVisibility={() =>
            setIsSceneControlsVisible(!isSceneControlsVisible)
          }
          sceneConfiguration={sceneConfiguration}
          onUpdateSceneConfiguration={updateSceneConfiguration}
        />

        <AssetSelection
          isVisible={isAssetSelectionVisible}
          selectedAsset={selectedAsset}
          onSelectAsset={setSelectedAsset}
          onToggleVisibility={() =>
            setIsAssetSelectionVisible(!isAssetSelectionVisible)
          }
        />

        <BottomControls
          isVisible={isBottomControlsVisible}
          onToggleVisibility={() =>
            setIsBottomControlsVisible(!isBottomControlsVisible)
          }
          onShootPreview={shootPreview}
          onPlaybackPreview={playbackPreview}
          assets={sceneConfiguration}
          onRemoveAsset={removeSceneConfiguration}
        />
      </ControlsOverlay>
    </div>
  );
}
