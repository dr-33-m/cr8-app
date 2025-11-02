import { MentionsInput, Mention } from "react-mentions";
import { Inbox, Image, Send } from "lucide-react";
import { useChatMessage } from "@/hooks/useChatMessage";
import { InboxPopover } from "./InboxPopover";
import useInboxStore from "@/store/inboxStore";
import useSceneContextStore from "@/store/sceneContextStore";

export function ChatInterface() {
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
        className={`px-3 py-2 flex items-center gap-3 rounded-md mx-1 ${
          focused
            ? "bg-accent text-accent-foreground"
            : "text-popover-foreground"
        }`}
      >
        <div className="shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-base bg-primary/20 border border-primary/30">
          <Inbox className="h-4 w-4 text-primary" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">
            {highlightedDisplay}
          </div>
          <div className="text-xs text-muted-foreground truncate">
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
        className={`px-3 py-2 flex items-center gap-3 rounded-md mx-1 ${
          focused
            ? "bg-accent text-accent-foreground"
            : "text-popover-foreground"
        }`}
      >
        <div className="shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-base bg-secondary/30 border border-secondary/50">
          <Image className="h-4 w-4 text-secondary-foreground" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="text-sm font-medium truncate">
            {highlightedDisplay}
          </div>
          <div className="text-xs text-muted-foreground truncate">
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
    <div className="flex justify-center col-span-3 max-w-md">
      <div className="w-full border rounded-lg bg-muted px-3 py-2 shadow-sm">
        {/* Input Section */}
        <div className="w-full mb-1">
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
            {/* Inbox mentions with @ trigger (primary color) */}
            <Mention
              trigger="@"
              data={inboxMentions}
              renderSuggestion={renderInboxSuggestion}
              displayTransform={(id, display) => `@${display}`}
              markup="@[__display__](__id__)"
              appendSpaceOnAdd
              style={inboxMentionStyle}
            />

            {/* Scene mentions with # trigger (secondary color) */}
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
        </div>

        {/* Action Buttons Row */}
        <div className="flex items-center justify-between w-full mt-4">
          {/* Left side - Inbox Button */}
          <InboxPopover />

          {/* Right side - Send Button */}
          <Send
            onClick={handleSendMessage}
            className={`h-4 w-4 cursor-pointer transition-colors duration-200 ${
              !message.trim() || isLoading
                ? "text-muted-foreground cursor-not-allowed"
                : "text-primary hover:text-primary/80"
            }`}
          />
        </div>
      </div>
    </div>
  );
}

// Styling for MentionsInput using theme variables
const mentionsInputStyle = {
  control: {
    fontSize: 14,
    fontWeight: "normal",
    minHeight: 32,
    maxHeight: 120,
    width: "100%",
  },
  "&multiLine": {
    control: {
      fontFamily: "inherit",
      minHeight: 32,
      maxHeight: 100,
      width: "100%",
    },
    highlighter: {
      padding: 12,
      overflow: "hidden",
      width: "100%",
    },
    input: {
      padding: 0,
      border: "none",
      borderRadius: 0,
      backgroundColor: "transparent",
      color: "var(--foreground)",
      outline: "none",
      resize: "none" as const,
      overflowX: "hidden",
      overflowY: "auto",
      whiteSpace: "pre-wrap",
      wordBreak: "break-word",
      width: "100%",
      minHeight: 32,
      maxHeight: 100,
      boxShadow: "none",
      boxSizing: "border-box",
    },
  },
  suggestions: {
    list: {
      backgroundColor: "var(--popover)",
      border: "1px solid var(--border)",
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

// Styling for inbox mentions (primary color)
const inboxMentionStyle = {
  borderBottom: "2px solid var(--primary)",
};

const sceneMentionStyle = {
  borderBottom: "2px solid var(--secondary)",
};
