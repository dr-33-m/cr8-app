import { useChatMessage } from "@/hooks/useChatMessage";
import useInboxStore from "@/store/inboxStore";
import useSceneContextStore from "@/store/sceneContextStore";
import { ChatInput } from "./ChatInput";
import { ChatActions } from "./ChatActions";
import {
  renderInboxSuggestion,
  renderSceneSuggestion,
} from "./MentionSuggestions";

export function BlazeChat() {
  const { message, setMessage, isLoading, handleSendMessage } =
    useChatMessage();

  const inboxItems = useInboxStore((state) => state.items);
  const sceneObjects = useSceneContextStore((state) => state.objects);

  // Prepare inbox mentions (primary color)
  const inboxMentions = inboxItems.map((item) => ({
    id: `inbox:${item.id}`,
    display: item.name,
    type: item.type,
    source: "inbox" as const,
  }));

  // Prepare scene mentions (secondary color for better visibility)
  const sceneMentions = sceneObjects.map((obj) => ({
    id: `scene:${obj.name}`,
    display: obj.name,
    type: obj.type,
    source: "scene" as const,
  }));

  return (
    <div className="flex justify-center col-span-3 max-w-md">
      <div className="w-full border rounded-lg bg-muted px-3 py-2 shadow-sm">
        {/* Input Section */}
        <ChatInput
          inboxMentions={inboxMentions}
          sceneMentions={sceneMentions}
          renderInboxSuggestion={renderInboxSuggestion}
          renderSceneSuggestion={renderSceneSuggestion}
          onSendMessage={handleSendMessage}
          message={message}
          setMessage={setMessage}
          isLoading={isLoading}
        />

        {/* Action Buttons Row */}
        <ChatActions
          onSendMessage={handleSendMessage}
          message={message}
          isLoading={isLoading}
        />
      </div>
    </div>
  );
}
