import { useState, useCallback } from "react";
import { toast } from "sonner";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import useInboxStore from "@/store/inboxStore";
import useBlazeChatStore from "@/store/blazeChatStore";
import { useSceneContext } from "@/hooks/useSceneContext";

import { MentionData } from "@/lib/types/bottomControls";

export function useChatMessage() {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const { sendMessage: wsSendMessage, isFullyConnected } =
    useWebSocketContext();
  const inboxStore = useInboxStore();
  const { objects: sceneObjects } = useSceneContext();

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

      const request = {
        message: plainTextMessage.trim(),
        context: {
          inbox_items: inboxItems,
          scene_objects: sceneContext,
          mentions: {
            assets: assetMentions,
            objects: objectMentions,
          },
        },
        route: "agent" as const,
        refresh_context: inboxItems.length > 0, // Refresh context when there are inbox items to process
      };

      // Send message to B.L.A.Z.E Agent with context
      wsSendMessage(request);

      // Record the turn and light up the activity indicator. isLoading below
      // only gates the input — it clears the moment this fire-and-forget emit
      // returns, so it says nothing about whether B.L.A.Z.E is still working.
      // The store's isBusy is what tracks that, and it clears on the response.
      const chat = useBlazeChatStore.getState();
      chat.addUser(plainTextMessage.trim());
      chat.setBusy(true);
      // Kept so a failed turn can be replayed verbatim — same context and
      // mentions, not just the message text.
      chat.setLastRequest(request);

      // Clear input
      setMessage("");

      // No "message sent" toast — the message is already visible in the chat
      // panel the instant addUser runs, and the Blaze mark starts pulsing.
    } catch (error) {
      console.error("Failed to send message:", error);
      toast.error("Failed to send message");
      // Nothing is in flight, so don't leave the indicator pulsing forever.
      useBlazeChatStore.getState().setBusy(false);
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
