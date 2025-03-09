import { useCallback } from "react";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { Animation } from "@/lib/types/animations";
import { toast } from "sonner";
import { fetchAnimations } from "@/lib/services/animationService";
import { createAnimationHandler } from "./useAnimationWebSocket";

export function useAnimations() {
  const { sendMessage } = useWebSocketContext();

  // Use the animation handler factory to create handlers
  const animationHandlers = createAnimationHandler(sendMessage);

  /**
   * Load animations of a specific type from the server
   */
  const loadAnimations = useCallback(
    async (type: "camera" | "light" | "product"): Promise<Animation[]> => {
      try {
        const animations = await fetchAnimations(type);
        return animations;
      } catch (error) {
        console.error(`Error loading ${type} animations:`, error);
        toast.error(`Failed to load ${type} animations`);
        return [];
      }
    },
    []
  );

  return {
    loadAnimations,
    applyAnimation: animationHandlers.applyAnimation,
    handleAnimationResponse: animationHandlers.handleAnimationResponse,
  };
}
