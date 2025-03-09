import { useCallback } from "react";
import { Animation } from "@/lib/types/animations";
import { toast } from "sonner";
import { WebSocketMessage } from "@/lib/types/websocket";

/**
 * Factory function to create animation handlers with a given sendMessage function
 * This breaks the circular dependency between WebSocketContext and useAnimations
 */
export function createAnimationHandler(
  sendMessageFn: (message: WebSocketMessage) => void
) {
  return {
    /**
     * Apply an animation to a target empty
     */
    applyAnimation: (animation: Animation, emptyName: string) => {
      try {
        // Create a unique message ID for tracking
        const messageId = `anim_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

        // Determine the command based on animation type
        const command = `load_${animation.template_type}_animation`;

        // Send the animation command via WebSocket with just the ID
        // The middleware will fetch the full template data
        sendMessageFn({
          command,
          empty_name: emptyName,
          animation_id: animation.id,
          message_id: messageId,
        });

        toast.success(
          `Applying ${animation.template_type} animation: ${animation.name}`
        );
      } catch (error) {
        console.error("Error applying animation:", error);
        toast.error("Failed to apply animation");
      }
    },

    /**
     * Handle animation response from WebSocket
     */
    handleAnimationResponse: (data: any) => {
      if (data.success) {
        toast.success("Animation applied successfully");
      } else {
        toast.error(`Animation failed: ${data.message || "Unknown error"}`);
      }
    },
  };
}
