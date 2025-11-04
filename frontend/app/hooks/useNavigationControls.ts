import { useState, useCallback } from "react";
import { toast } from "sonner";
import { useWebSocketContext } from "@/contexts/WebSocketContext";

import { ViewportMode } from "@/lib/types/bottomControls";

export function useNavigationControls() {
  const [viewportMode, setViewportMode] = useState<ViewportMode>("solid");
  const { sendMessage, isFullyConnected } = useWebSocketContext();

  const sendNavigationCommand = useCallback(
    async (command: string) => {
      if (!isFullyConnected) return;

      try {
        sendMessage({
          type: "addon_command",
          addon_id: "blender_ai_router",
          command: command,
          params: {},
        });
      } catch (error) {
        toast.error(`Failed to send ${command} command`);
      }
    },
    [isFullyConnected, sendMessage]
  );

  // Viewport controls
  const handleViewportSolid = useCallback(() => {
    if (viewportMode !== "solid") {
      sendNavigationCommand("viewport_set_solid");
      setViewportMode("solid");
    }
  }, [viewportMode, sendNavigationCommand]);

  const handleViewportRendered = useCallback(() => {
    if (viewportMode !== "rendered") {
      sendNavigationCommand("viewport_set_rendered");
      setViewportMode("rendered");
    }
  }, [viewportMode, sendNavigationCommand]);

  // 3D Navigation controls
  const handleZoomIn = useCallback(
    () => sendNavigationCommand("zoom_in"),
    [sendNavigationCommand]
  );

  const handleZoomOut = useCallback(
    () => sendNavigationCommand("zoom_out"),
    [sendNavigationCommand]
  );

  const handlePanUp = useCallback(
    () => sendNavigationCommand("pan_up"),
    [sendNavigationCommand]
  );

  const handlePanDown = useCallback(
    () => sendNavigationCommand("pan_down"),
    [sendNavigationCommand]
  );

  const handlePanLeft = useCallback(
    () => sendNavigationCommand("pan_left"),
    [sendNavigationCommand]
  );

  const handlePanRight = useCallback(
    () => sendNavigationCommand("pan_right"),
    [sendNavigationCommand]
  );

  const handleOrbitLeft = useCallback(
    () => sendNavigationCommand("orbit_left"),
    [sendNavigationCommand]
  );

  const handleOrbitRight = useCallback(
    () => sendNavigationCommand("orbit_right"),
    [sendNavigationCommand]
  );

  const handleOrbitUp = useCallback(
    () => sendNavigationCommand("orbit_up"),
    [sendNavigationCommand]
  );

  const handleOrbitDown = useCallback(
    () => sendNavigationCommand("orbit_down"),
    [sendNavigationCommand]
  );

  return {
    viewportMode,
    handleViewportSolid,
    handleViewportRendered,
    handleZoomIn,
    handleZoomOut,
    handlePanUp,
    handlePanDown,
    handlePanLeft,
    handlePanRight,
    handleOrbitLeft,
    handleOrbitRight,
    handleOrbitUp,
    handleOrbitDown,
  };
}
