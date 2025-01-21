import { useSceneConfigStore } from "@/store/sceneConfiguratorStore";
import { useState, useCallback } from "react";

export const usePreviewRenderer = (websocket: WebSocket | null) => {
  const [isLoading, setIsLoading] = useState(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPreviewAvailable, setIsPreviewAvailable] = useState(false);
  const { resetSceneConfiguration } = useSceneConfigStore();

  const shootPreview = (sceneConfiguration: any) => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(
        JSON.stringify({
          command: "start_preview_rendering",
          params: {
            resolution_x: 1280,
            resolution_y: 720,
            samples: 128,
            num_frames: 100,
            subcommands: sceneConfiguration,
          },
        })
      );
      resetSceneConfiguration();
      setIsLoading(true);
    } else {
      console.error("WebSocket is not open");
      setIsLoading(false);
    }
  };

  const playbackPreview = useCallback(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({ command: "start_broadcast" }));
      setIsPlaying(true);
    } else {
      console.error("WebSocket is not open");
    }
  }, [websocket]);

  const stopPlaybackPreview = useCallback(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({ command: "stop_broadcast" }));
      setIsPlaying(false);
    } else {
      console.error("WebSocket is not open");
    }
  }, [websocket]);

  const generateVideo = useCallback(() => {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.send(JSON.stringify({ command: "generate_video" }));
      setIsLoading(true);
    } else {
      console.error("WebSocket is not open");
      setIsLoading(false);
    }
  }, [websocket]);

  return {
    isLoading,
    isPlaying,
    isPreviewAvailable,
    setIsPreviewAvailable,
    setIsLoading,
    shootPreview,
    playbackPreview,
    stopPlaybackPreview,
    generateVideo,
  };
};
