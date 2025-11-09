import { useState, useCallback } from "react";
import { toast } from "sonner";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import useInboxStore from "@/store/inboxStore";
import useSceneContextStore from "@/store/sceneContextStore";

import { MentionData } from "@/lib/types/bottomControls";

export function useChatMessage() {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { sendMessage: wsSendMessage, isFullyConnected } =
    useWebSocketContext();
  const inboxStore = useInboxStore();
  const sceneObjects = useSceneContextStore((state) => state.objects);

  // Parse mentions from react-mentions markup format
  const parseMentions = useCallback(
    (text: string) => {
      const mentions: MentionData[] = [];

      // Match inbox mentions: @[display](inbox:id)
      const inboxRegex = /@\[([^\]]+)\]\(inbox:([^)]+)\)/g;
      let match;

      while ((match = inboxRegex.exec(text)) !== null) {
        const display = match[1];
        const id = match[2];

        const inboxItem = inboxStore.items.find((item) => item.id === id);
        if (inboxItem) {
          mentions.push({
            id: inboxItem.id,
            name: inboxItem.name,
            type: "inbox",
            itemType: inboxItem.type,
            source: "inbox",
          });
        }
      }

      // Match scene mentions: #[display](scene:name)
      const sceneRegex = /#\[([^\]]+)\]\(scene:([^)]+)\)/g;
      while ((match = sceneRegex.exec(text)) !== null) {
        const display = match[1];
        const name = match[2];

        const sceneObject = sceneObjects.find((obj) => obj.name === name);
        if (sceneObject) {
          mentions.push({
            id: sceneObject.name,
            name: sceneObject.name,
            type: "scene",
            itemType: sceneObject.type,
            source: "scene",
          });
        }
      }

      return mentions;
    },
    [inboxStore.items, sceneObjects]
  );

  // Convert markup to plain text for display
  const getPlainText = useCallback((text: string) => {
    // Convert @[Display](inbox:id) to @Display
    let plainText = text.replace(/@\[([^\]]+)\]\(inbox:[^)]+\)/g, "@$1");
    // Convert #[Display](scene:name) to #Display
    plainText = plainText.replace(/#\[([^\]]+)\]\(scene:[^)]+\)/g, "#$1");
    return plainText;
  }, []);

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

      // Parse mentions from message markup
      const mentions = parseMentions(message);

      // Separate mentions by type
      const assetMentions = mentions.filter((m) => m.type === "inbox");
      const objectMentions = mentions.filter((m) => m.type === "scene");

      // Convert to plain text for the agent
      const plainTextMessage = getPlainText(message);

      // Send message to B.L.A.Z.E Agent with context
      wsSendMessage({
        message: plainTextMessage.trim(),
        context: {
          inbox_items: inboxItems,
          scene_objects: sceneContext,
          mentions: {
            assets: assetMentions,
            objects: objectMentions,
          },
        },
        route: "agent",
        refresh_context: inboxItems.length > 0, // Refresh context when there are inbox items to process
      });

      // Clear input
      setMessage("");

      // Build context summary for toast
      const contextParts: string[] = [];

      if (assetMentions.length > 0) {
        contextParts.push(
          `${assetMentions.length} asset${
            assetMentions.length !== 1 ? "s" : ""
          }`
        );
      }

      if (objectMentions.length > 0) {
        contextParts.push(
          `${objectMentions.length} object${
            objectMentions.length !== 1 ? "s" : ""
          }`
        );
      }

      if (inboxItems.length > 0 && assetMentions.length === 0) {
        contextParts.push(
          `${inboxItems.length} inbox item${inboxItems.length !== 1 ? "s" : ""}`
        );
      }

      if (sceneContext.length > 0 && objectMentions.length === 0) {
        contextParts.push(
          `${sceneContext.length} scene object${
            sceneContext.length !== 1 ? "s" : ""
          }`
        );
      }

      const contextSummary =
        contextParts.length > 0 ? ` (${contextParts.join(", ")})` : "";

      toast.success(`Message sent to B.L.A.Z.E${contextSummary}`);
    } catch (error) {
      console.error("Failed to send message:", error);
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
    parseMentions,
    getPlainText,
  ]);

  return {
    message,
    setMessage,
    isLoading,
    handleSendMessage,
  };
}
