import { createFileRoute } from "@tanstack/react-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { PreviewWindow } from "@/components/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/FullScreenToggle";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { AssetSelection } from "@/components/creative-workspace/AssetSelection";
import { BottomControls } from "@/components/BottomControls";
import {
  OnRemoveAssetFunction,
  SceneConfiguration,
} from "@/lib/types/sceneConfig";
import { SceneViewPort } from "@/components/creative-workspace/SceneViewPort";
import { SceneActions } from "@/components/creative-workspace/SceneActions";

export const Route = createFileRoute("/project/")({
  component: RouteComponent,
});

function RouteComponent() {
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  const [sceneConfiguration, setSceneConfiguration] =
    useState<SceneConfiguration>({});
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const videoUrl = "";
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isPreviewAvailable, setIsPreviewAvailable] = useState<boolean>(false);

  useEffect(() => {
    // Establish WebSocket connection
    const ws = new WebSocket("ws://localhost:8000/ws/browser");
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
          setIsLoading(false);
        } else if (data.type === "viewport_stream_error") {
          console.error("Viewport stream error:", data.message);
          setIsLoading(false);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
        setIsLoading(false);
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
      setSceneConfiguration({});
      setIsLoading(true);
    } else {
      console.error("WebSocket is not open");
      setIsLoading(false);
    }
  };

  const playbackPreview = useCallback(() => {
    if (
      websocketRef.current &&
      websocketRef.current.readyState === WebSocket.OPEN
    ) {
      try {
        websocketRef.current.send(
          JSON.stringify({
            command: "start_broadcast",
          })
        );
        setIsPlaying(true);
      } catch (error) {
        console.error("Failed to send WebSocket message:", error);
      }
    } else {
      console.error("WebSocket is not open");
    }
  }, [websocketRef]);

  const stopPlaybackPreview = useCallback(() => {
    if (
      websocketRef.current &&
      websocketRef.current.readyState === WebSocket.OPEN
    ) {
      try {
        websocketRef.current.send(
          JSON.stringify({
            command: "stop_broadcast",
          })
        );
        setIsPlaying(false);
      } catch (error) {
        console.error("Failed to send WebSocket message:", error);
      }
    } else {
      console.error("WebSocket is not open");
    }
  }, [websocketRef]);

  const generateVideo = useCallback(() => {
    if (
      websocketRef.current &&
      websocketRef.current.readyState === WebSocket.OPEN
    ) {
      try {
        websocketRef.current.send(
          JSON.stringify({
            command: "generate_video",
          })
        );
        setIsLoading(true);
      } catch (error) {
        console.error("Failed to send WebSocket message:", error);
        setIsLoading(false);
      }
    } else {
      console.error("WebSocket is not open");
      setIsLoading(false);
    }
  }, [websocketRef]);

  const updateSceneConfiguration = (
    key: keyof SceneConfiguration,
    value: any
  ) => {
    setSceneConfiguration((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const removeSceneConfiguration: OnRemoveAssetFunction = (
    assetType,
    assetId
  ) => {
    setSceneConfiguration((prev) => {
      const newConfig = { ...prev };

      switch (assetType) {
        case "camera":
          delete newConfig.camera;
          break;
        case "light":
          delete newConfig.lights;
          break;
      }

      return newConfig;
    });
  };

  return (
    <div className="relative w-full h-screen bg-[#1C1C1C] text-white">
      <PreviewWindow>
        <SceneViewPort
          canvasRef={canvasRef}
          isPreviewAvailable={isPreviewAvailable}
          finalVideoUrl={videoUrl}
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
            onShootPreview={shootPreview}
            onPlaybackPreview={playbackPreview}
            onStopPlaybackPreview={stopPlaybackPreview}
            onGenerateVideo={generateVideo}
            assets={sceneConfiguration}
            onRemoveAsset={removeSceneConfiguration}
            isLoading={isLoading}
            isPlaying={isPlaying}
            isFinalVideoReady={!!videoUrl}
          />
        </BottomControls>
      </ControlsOverlay>
    </div>
  );
}
