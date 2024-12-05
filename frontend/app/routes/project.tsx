import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useRef, useState } from "react";
import { PreviewWindow } from "@/components/creative-workspace/PreviewWindow";
import { ControlsOverlay } from "@/components/creative-workspace/ControlsOverlay";
import { SceneControls } from "@/components/creative-workspace/SceneControls";
import { AssetSelection } from "@/components/creative-workspace/AssetSelection";
import { BottomControls } from "@/components/creative-workspace/BottomControls";

export const Route = createFileRoute("/project")({
  component: RouteComponent,
});

type SceneControl = {
  name: string;
  icon: React.ReactNode;
  color: string;
  control: React.ReactNode;
};

function RouteComponent() {
  const [selectedAsset, setSelectedAsset] = useState<number | null>(null);
  const [isSceneControlsVisible, setIsSceneControlsVisible] =
    useState<boolean>(true);
  const [isAssetSelectionVisible, setIsAssetSelectionVisible] =
    useState<boolean>(true);
  const [isBottomControlsVisible, setIsBottomControlsVisible] =
    useState<boolean>(true);
  const [isFullscreen, setIsFullscreen] = useState<boolean>(false);
  const [viewportImage, setViewportImage] = useState<string | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);

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
          // Directly use base64 data
          setViewportImage(`data:image/png;base64,${data.data}`);
        } else if (data.type === "viewport_stream_error") {
          console.error("Viewport stream error:", data.message);
          setViewportImage(null);
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

  const handleStreamViewport = () => {
    if (
      websocketRef.current &&
      websocketRef.current.readyState === WebSocket.OPEN
    ) {
      websocketRef.current.send(
        JSON.stringify({
          // command: "start_preview_rendering",
          // params: {
          //   resolution_x: 1920,
          //   resolution_y: 1080,
          //   samples: 16,
          //   num_frames: 40,
          // },
          command: "start_broadcast",
        })
      );
    } else {
      console.error("WebSocket is not open");
    }
  };

  return (
    <div className="relative w-full h-screen bg-[#1C1C1C] text-white overflow-hidden">
      <PreviewWindow
        isFullscreen={isFullscreen}
        viewportImage={viewportImage}
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
          onStreamViewport={handleStreamViewport}
        />
      </ControlsOverlay>
    </div>
  );
}
