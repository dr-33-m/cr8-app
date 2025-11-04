import { MentionsInput, Mention } from "react-mentions";
import { useChatMessage } from "@/hooks/useChatMessage";
import {
  inboxMentionStyle,
  mentionsInputStyle,
  sceneMentionStyle,
} from "./chatStyles";

interface ChatInputProps {
  inboxMentions: Array<{
    id: string;
    display: string;
    type: string;
    source: "inbox";
  }>;
  sceneMentions: Array<{
    id: string;
    display: string;
    type: string;
    source: "scene";
  }>;
  renderInboxSuggestion: (
    suggestion: any,
    search: string,
    highlightedDisplay: React.ReactNode,
    index: number,
    focused: boolean
  ) => React.ReactNode;
  renderSceneSuggestion: (
    suggestion: any,
    search: string,
    highlightedDisplay: React.ReactNode,
    index: number,
    focused: boolean
  ) => React.ReactNode;
  onSendMessage: () => void;
}

export function ChatInput({
  inboxMentions,
  sceneMentions,
  renderInboxSuggestion,
  renderSceneSuggestion,
  onSendMessage,
}: ChatInputProps) {
  const { message, setMessage, isLoading } = useChatMessage();

  // Handle key press for Enter to send
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      onSendMessage();
    }
  };

  return (
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
  );
}
