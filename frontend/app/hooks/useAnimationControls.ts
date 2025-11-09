import { useState, useCallback } from "react";
import { toast } from "sonner";
import { useWebSocketContext } from "@/contexts/WebSocketContext";

import { AnimationState } from "@/lib/types/bottomControls";

export function useAnimationControls() {
  const [animationState, setAnimationState] =
    useState<AnimationState>("paused");
  const { sendMessage, isFullyConnected } = useWebSocketContext();

  const sendNavigationCommand = useCallback(
    async (command: string) => {
      if (!isFullyConnected) return;

      try {
        sendMessage({
          command: command,
          params: {},
          route: "direct",
        });
      } catch (error) {
        toast.error(`Failed to send ${command} command`);
      }
    },
    [isFullyConnected, sendMessage]
  );

  const handleFrameJumpStart = useCallback(
    () => sendNavigationCommand("frame_jump_start"),
    [sendNavigationCommand]
  );

  const handleFrameJumpEnd = useCallback(
    () => sendNavigationCommand("frame_jump_end"),
    [sendNavigationCommand]
  );

  const handleKeyframeJumpPrev = useCallback(
    () => sendNavigationCommand("keyframe_jump_prev"),
    [sendNavigationCommand]
  );

  const handleKeyframeJumpNext = useCallback(
    () => sendNavigationCommand("keyframe_jump_next"),
    [sendNavigationCommand]
  );

  const handleAnimationPlay = useCallback(() => {
    if (animationState === "playing") {
      sendNavigationCommand("animation_pause");
      setAnimationState("paused");
    } else {
      sendNavigationCommand("animation_play");
      setAnimationState("playing");
    }
  }, [animationState, sendNavigationCommand]);

  const handleAnimationPlayReverse = useCallback(() => {
    sendNavigationCommand("animation_play_reverse");
    setAnimationState("playing_reverse");
  }, [sendNavigationCommand]);

  return {
    animationState,
    handleFrameJumpStart,
    handleFrameJumpEnd,
    handleKeyframeJumpPrev,
    handleKeyframeJumpNext,
    handleAnimationPlay,
    handleAnimationPlayReverse,
  };
}
