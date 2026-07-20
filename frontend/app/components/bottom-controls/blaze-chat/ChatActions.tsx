import { Send } from "lucide-react";
import { InboxPopover } from "../InboxPopover";

import { ChatActionsProps } from "@/lib/types/bottomControls";

export function ChatActions({
  onSendMessage,
  message,
  isLoading,
  disabled = false,
}: ChatActionsProps) {
  const isSendDisabled = !message.trim() || isLoading || disabled;

  return (
    <div className="flex items-center justify-between w-full mt-4">
      {/* Left side - Inbox Button */}
      <InboxPopover />

      {/* Right side - Send Button */}
      <Send
        onClick={isSendDisabled ? undefined : onSendMessage}
        className={`h-4 w-4 transition-colors duration-200 ${
          isSendDisabled
            ? "text-muted-foreground cursor-not-allowed"
            : "text-primary hover:text-primary/80 cursor-pointer"
        }`}
      />
    </div>
  );
}
