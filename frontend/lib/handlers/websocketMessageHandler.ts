import {
  AnimationResponseMessage,
  WebSocketMessage,
} from "@/lib/types/websocket";
import { toast } from "sonner";

/**
 * Process WebSocket messages and route them to appropriate handlers
 */
export function processWebSocketMessage(
  data: WebSocketMessage,
  handlers: {
    onAnimationResponse?: (data: AnimationResponseMessage) => void;
    onTemplateControls?: (data: any) => void;
    onAssetOperationResponse?: (data: any) => void;
    onPreviewFrame?: (data: any) => void;
    onBroadcastComplete?: () => void;
    onError?: (message: string) => void;
    [key: string]: ((data: any) => void) | undefined;
  }
) {
  try {
    // Handle error messages
    if (data.status === "ERROR") {
      if (handlers.onError) {
        handlers.onError(data.message || "Unknown error");
      } else {
        toast.error(data.message || "Unknown error");
      }
      return;
    }

    // Handle animation responses
    if (
      data.command === "camera_animation_result" ||
      data.command === "light_animation_result" ||
      data.command === "product_animation_result"
    ) {
      if (handlers.onAnimationResponse) {
        handlers.onAnimationResponse(data as AnimationResponseMessage);
      }
      return;
    }

    // Handle template controls response
    if (data.command === "template_controls_result") {
      if (handlers.onTemplateControls) {
        handlers.onTemplateControls(data);
      }
      return;
    }

    // Handle B.L.A.Z.E Agent responses
    if (data.type === "agent_response") {
      if (handlers.onAgentResponse) {
        handlers.onAgentResponse(data);
      }
      return;
    }

    // Handle asset operation responses
    if (
      data.command?.endsWith("_result") &&
      [
        "append_asset_result",
        "remove_assets_result",
        "swap_assets_result",
        "rotate_assets_result",
        "scale_assets_result",
        "asset_info_result",
      ].includes(data.command)
    ) {
      if (handlers.onAssetOperationResponse) {
        handlers.onAssetOperationResponse(data);
      }
      return;
    }

    // Handle preview frames
    if (data.type === "frame") {
      if (handlers.onPreviewFrame) {
        handlers.onPreviewFrame(data);
      }
      return;
    }

    // Handle broadcast complete
    if (data.type === "broadcast_complete") {
      if (handlers.onBroadcastComplete) {
        handlers.onBroadcastComplete();
      }
      return;
    }

    // Handle custom handlers
    const customHandler = handlers[`on${data.command}`];
    if (customHandler) {
      customHandler(data);
      return;
    }

    // Log unhandled messages
    console.log("Unhandled WebSocket message:", data);
  } catch (error) {
    console.error("Error processing WebSocket message:", error);
    toast.error("Error processing message from server");
  }
}
