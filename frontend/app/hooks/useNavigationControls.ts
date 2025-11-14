import { useCallback } from "react";
import { toast } from "sonner";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { useNavigationStore } from "@/store/navigationStore";

export function useNavigationControls() {
  const {
    viewportMode,
    topButtonDirection,
    bottomButtonDirection,
    panAmount,
    setViewportMode,
    setTopButtonDirection,
    setBottomButtonDirection,
    setPanAmount,
    toggleTopButtonDirection,
    toggleBottomButtonDirection,
  } = useNavigationStore();

  const { sendMessage, isFullyConnected } = useWebSocketContext();

  const sendNavigationCommand = useCallback(
    async (command: string, params: Record<string, any> = {}) => {
      if (!isFullyConnected) return;

      try {
        sendMessage({
          command: command,
          params: params,
          route: "direct",
          addon_id: "blender_controls",
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
  }, [viewportMode, sendNavigationCommand, setViewportMode]);

  const handleViewportRendered = useCallback(() => {
    if (viewportMode !== "rendered") {
      sendNavigationCommand("viewport_set_rendered");
      setViewportMode("rendered");
    }
  }, [viewportMode, sendNavigationCommand, setViewportMode]);

  // 3D Navigation controls - using getState() to access current values
  const handleZoomIn = useCallback(
    () => sendNavigationCommand("zoom_in"),
    [sendNavigationCommand]
  );

  const handleZoomOut = useCallback(
    () => sendNavigationCommand("zoom_out"),
    [sendNavigationCommand]
  );

  const handlePanUp = useCallback(() => {
    const { topButtonDirection, panAmount } = useNavigationStore.getState();
    sendNavigationCommand("pan_up_forward", {
      direction: topButtonDirection,
      amount: panAmount,
    });
  }, [sendNavigationCommand]);

  const handlePanDown = useCallback(() => {
    const { bottomButtonDirection, panAmount } = useNavigationStore.getState();
    sendNavigationCommand("pan_down_backward", {
      direction: bottomButtonDirection,
      amount: panAmount,
    });
  }, [sendNavigationCommand]);

  const handlePanLeft = useCallback(() => {
    const { panAmount } = useNavigationStore.getState();
    sendNavigationCommand("pan_left", { amount: panAmount });
  }, [sendNavigationCommand]);

  const handlePanRight = useCallback(() => {
    const { panAmount } = useNavigationStore.getState();
    sendNavigationCommand("pan_right", { amount: panAmount });
  }, [sendNavigationCommand]);

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
    topButtonDirection,
    bottomButtonDirection,
    setTopButtonDirection,
    setBottomButtonDirection,
    panAmount,
    setPanAmount,
    toggleTopButtonDirection,
    toggleBottomButtonDirection,
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
