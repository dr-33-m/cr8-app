import { MentionsInput, Mention } from "react-mentions";
import { SendHorizontal, Inbox, Gamepad2, Image } from "lucide-react";
import { useChatMessage } from "@/hooks/useChatMessage";
import { InboxPopover } from "./InboxPopover";
import useInboxStore from "@/store/inboxStore";
import useSceneContextStore from "@/store/sceneContextStore";

export function ChatInterface() {
  const { message, setMessage, isLoading, handleSendMessage } =
    useChatMessage();

  const inboxItems = useInboxStore((state) => state.items);
  const sceneObjects = useSceneContextStore((state) => state.objects);

  // Prepare inbox mentions (blue)
  const inboxMentions = inboxItems.map((item) => ({
    id: `inbox:${item.id}`,
    display: item.name,
    type: item.type,
    source: "inbox" as const,
  }));

  // Prepare scene mentions (green)
  const sceneMentions = sceneObjects.map((obj) => ({
    id: `scene:${obj.name}`,
    display: obj.name,
    type: obj.type,
    source: "scene" as const,
  }));

  // Custom suggestion renderer for inbox items
  const renderInboxSuggestion = (
    suggestion: any,
    search: string,
    highlightedDisplay: React.ReactNode,
    index: number,
    focused: boolean
  ) => {
    return (
      <div
        className={`px-3 py-2 flex items-center gap-3 rounded-lg mx-1 ${
          focused
            ? "bg-cr8-blue/20 text-white backdrop-blur-xs"
            : "text-white/80"
        }`}
      >
        <div className="shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-base bg-cr8-blue/10 backdrop-blur-xs border border-cr8-blue/20">
          <Inbox className="h-4 w-4 text-cr8-blue" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">
            {highlightedDisplay}
          </div>
          <div className="text-xs text-cr8-blue/70 truncate">
            {suggestion.type} • inbox
          </div>
        </div>
      </div>
    );
  };

  // Custom suggestion renderer for scene objects
  const renderSceneSuggestion = (
    suggestion: any,
    search: string,
    highlightedDisplay: React.ReactNode,
    index: number,
    focused: boolean
  ) => {
    return (
      <div
        className={`px-3 py-2 flex items-center gap-3 rounded-lg mx-1 ${
          focused
            ? "bg-green-500/20 text-white backdrop-blur-xs"
            : "text-white/80"
        }`}
      >
        <div className="shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-base bg-green-500/10 backdrop-blur-xs border border-green-500/20">
          <Image className="h-4 w-4 text-green-500" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">
            {highlightedDisplay}
          </div>
          <div className="text-xs text-green-400/70 truncate">
            {suggestion.type} • scene
          </div>
        </div>
      </div>
    );
  };

  // Handle key press for Enter to send
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div className="relative flex justify-center col-span-3">
      <div className="relative w-full">
        <MentionsInput
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isLoading}
          placeholder="Tell B.L.A.Z.E what to do... (Use @inbox or #scene)"
          a11ySuggestionsListLabel="Mention suggestions"
          allowSuggestionsAboveCursor
          style={mentionsInputStyle}
        >
          {/* Inbox mentions with @ trigger (blue) */}
          <Mention
            trigger="@"
            data={inboxMentions}
            renderSuggestion={renderInboxSuggestion}
            displayTransform={(id, display) => `@${display}`}
            markup="@[__display__](__id__)"
            appendSpaceOnAdd
            style={inboxMentionStyle}
          />

          {/* Scene mentions with # trigger (green) */}
          <Mention
            trigger="#"
            data={sceneMentions}
            renderSuggestion={renderSceneSuggestion}
            displayTransform={(id, display) => `#${display}`}
            markup="#[__display__](__id__)"
            appendSpaceOnAdd
            style={sceneMentionStyle}
          />
        </MentionsInput>

        {/* Inbox Button */}
        <InboxPopover />

        {/* Send Button */}
        <SendHorizontal
          onClick={handleSendMessage}
          className={`absolute right-3 top-3 h-4 w-4 cursor-pointer transition-colors duration-200 z-10 ${
            !message.trim() || isLoading
              ? "text-gray-500 cursor-not-allowed"
              : "text-primary hover:text-primary"
          }`}
        />
      </div>
    </div>
  );
}

// Styling for MentionsInput
const mentionsInputStyle = {
  control: {
    fontSize: 14,
    fontWeight: "normal",
    minHeight: 80,
    maxHeight: 120,
  },
  "&multiLine": {
    control: {
      fontFamily: "inherit",
      minHeight: 80,
      maxHeight: 120,
    },
    highlighter: {
      padding: 12,
      overflow: "hidden",
    },
    input: {
      padding: 12,
      paddingRight: 80,
      border: "1px solid rgba(255, 255, 255, 0.1)",
      borderRadius: 12,
      backgroundColor: "rgba(24, 24, 27, 0.1)",
      backdropFilter: "blur(12px)",
      color: "white",
      outline: "none",
      resize: "none" as const,
      overflow: "auto",
      minHeight: 80,
      maxHeight: 120,
      boxShadow: "0 10px 15px -3px rgb(0 0 0 / 0.1)",
    },
  },
  suggestions: {
    list: {
      backgroundColor: "rgba(24, 24, 27, 0.95)",
      backdropFilter: "blur(12px)",
      border: "1px solid rgba(255, 255, 255, 0.1)",
      boxShadow: "0 20px 25px -5px rgb(0 0 0 / 0.3)",
      fontSize: 14,
      overflow: "auto",
      maxHeight: 256,
      padding: "8px 0",
      minWidth: 280,
      maxWidth: 400,
    },
    item: {
      padding: 0,
      borderBottom: "none",
      "&focused": {
        backgroundColor: "transparent",
      },
    },
  },
};

// Styling for inbox mentions (blue) - glassmorphism style
const inboxMentionStyle = {
  borderBottom: "2px solid rgba(0, 119, 182, 0.95)",
};

const sceneMentionStyle = {
  borderBottom: "2px solid rgba(34, 197, 94, 0.95)",
};
