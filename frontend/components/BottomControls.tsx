import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChevronDown, ChevronUp, Send, Bot } from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { ConnectionStatus } from "./ConnectionStatus";
import { useState } from "react";
import { toast } from "sonner";

interface BottomControlsProps {
  children?: React.ReactNode;
}

export function BottomControls({ children }: BottomControlsProps) {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  const isVisible = useVisibilityStore(
    (state) => state.isBottomControlsVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleBottomControls
  );

  // Get WebSocket context directly - this component is now only used within WebSocketProvider
  const { status, reconnect, sendMessage, isFullyConnected } =
    useWebSocketContext();

  const handleSendMessage = async () => {
    if (!message.trim() || !isFullyConnected || isLoading) return;

    setIsLoading(true);
    try {
      // Send message to B.L.A.Z.E Agent
      sendMessage({
        type: "agent_message",
        message: message.trim(),
      });

      // Clear input
      setMessage("");
      toast.success("Message sent to B.L.A.Z.E");
    } catch (error) {
      toast.error("Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  return (
    <div
      className={`absolute bottom-4 left-1/2 transform -translate-x-1/2 transition-all duration-300 
      ${isVisible ? "translate-y-0" : "translate-y-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute left-1/2 -top-12 -translate-x-1/2 text-white hover:bg-white/10"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronDown className="h-6 w-6" />
        ) : (
          <ChevronUp className="h-6 w-6" />
        )}
      </Button>
      <div className="backdrop-blur-md bg-white/5 rounded-lg px-6 py-3 flex items-center gap-4">
        <ConnectionStatus status={status} />
        <div className="h-8 w-px bg-white/20" />

        {status === "disconnected" ? (
          <Button
            variant="secondary"
            onClick={reconnect}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            Reconnect
          </Button>
        ) : isFullyConnected ? (
          /* B.L.A.Z.E Chat Interface */
          <div className="flex items-center gap-2">
            <Bot className="h-5 w-5 text-blue-400" />
            <span className="text-white text-sm font-medium">B.L.A.Z.E</span>
            <Input
              placeholder="Tell B.L.A.Z.E what to do..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              className="min-w-[300px] bg-white/10 border-white/20 text-white placeholder:text-white/60"
              disabled={isLoading}
            />
            <Button
              onClick={handleSendMessage}
              disabled={!message.trim() || isLoading}
              size="icon"
              className="bg-blue-500 hover:bg-blue-600 disabled:opacity-50"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div className="text-white/60 text-sm">
            Waiting for Blender connection...
          </div>
        )}
      </div>
    </div>
  );
}
