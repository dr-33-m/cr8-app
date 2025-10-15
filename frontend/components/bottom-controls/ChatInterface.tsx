import { Textarea } from "@/components/ui/textarea";
import { SendHorizontal } from "lucide-react";
import { useChatMessage } from "@/hooks/useChatMessage";
import { InboxPopover } from "./InboxPopover";

export function ChatInterface() {
  const {
    message,
    setMessage,
    isLoading,
    textareaRef,
    handleSendMessage,
    handleKeyPress,
  } = useChatMessage();

  return (
    <div className="relative flex justify-center col-span-3">
      <Textarea
        ref={textareaRef}
        placeholder="Tell B.L.A.Z.E what to do..."
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        onKeyPress={handleKeyPress}
        className="w-full min-h-[80px] max-h-[120px] resize-none bg-cr8-charcoal/10 border-white/10 backdrop-blur-md shadow-lg text-white placeholder:text-white/60 overflow-hidden"
        disabled={isLoading}
      />

      {/* Inbox Button */}
      <InboxPopover />

      {/* Send Button */}
      <SendHorizontal
        onClick={handleSendMessage}
        className={`absolute right-3 top-3 h-4 w-4 cursor-pointer transition-colors duration-200 ${
          !message.trim() || isLoading
            ? "text-gray-500 cursor-not-allowed"
            : "text-primary hover:text-primary"
        }`}
      />
    </div>
  );
}
