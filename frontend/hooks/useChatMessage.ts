import { useState, useRef, useEffect, useCallback } from "react";
import { toast } from "sonner";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import useInboxStore from "@/store/inboxStore";
import useSceneContextStore from "@/store/sceneContextStore";

export function useChatMessage() {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const { sendMessage: wsSendMessage, isFullyConnected } =
    useWebSocketContext();
  const inboxStore = useInboxStore();
  const sceneObjects = useSceneContextStore((state) => state.objects);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        textareaRef.current.scrollHeight + "px";
    }
  }, [message]);

  const handleSendMessage = useCallback(async () => {
    if (!message.trim() || !isFullyConnected || isLoading) return;

    setIsLoading(true);
    try {
      // Get inbox items for context
      const inboxItems = inboxStore.items.map((item) => ({
        id: item.id,
        name: item.name,
        type: item.type,
        registry: item.registry,
      }));

      // Get scene objects for context
      const sceneContext = sceneObjects.map((obj) => ({
        name: obj.name,
        type: obj.type,
        selected: obj.selected,
        active: obj.active,
        visible: obj.visible,
      }));

      // Send message to B.L.A.Z.E Agent with context
      wsSendMessage({
        type: "agent_message",
        message: message.trim(),
        context: {
          inbox_items: inboxItems,
          scene_objects: sceneContext,
        },
      });

      // Clear input
      setMessage("");

      // Show context summary in toast
      const contextParts: string[] = [];
      if (inboxItems.length > 0) {
        contextParts.push(
          `${inboxItems.length} inbox item${inboxItems.length !== 1 ? "s" : ""}`
        );
      }
      if (sceneContext.length > 0) {
        contextParts.push(
          `${sceneContext.length} scene object${sceneContext.length !== 1 ? "s" : ""}`
        );
      }

      const contextSummary =
        contextParts.length > 0 ? ` (with ${contextParts.join(" and ")})` : "";

      toast.success(`Message sent to B.L.A.Z.E${contextSummary}`);
    } catch (error) {
      toast.error("Failed to send message");
    } finally {
      setIsLoading(false);
    }
  }, [
    message,
    isFullyConnected,
    isLoading,
    wsSendMessage,
    inboxStore.items,
    sceneObjects,
  ]);

  const handleKeyPress = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
      }
    },
    [handleSendMessage]
  );

  return {
    message,
    setMessage,
    isLoading,
    textareaRef,
    handleSendMessage,
    handleKeyPress,
  };
}
