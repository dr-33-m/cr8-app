import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ChevronDown, ChevronUp, SendHorizontal } from "lucide-react";
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
          /* Chat Interface */
          <div className="relative">
            <Input
              placeholder="Tell B.L.A.Z.E what to do..."
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              className="min-w-[300px] pr-10 bg-cr8-charcoal/10 border-white/10 backdrop-blur-md shadow-lg text-white placeholder:text-white/60"
              disabled={isLoading}
            />
            <SendHorizontal
              onClick={handleSendMessage}
              className={`absolute right-3 top-1/2 -translate-y-1/2 h-4 w-4 cursor-pointer transition-colors duration-200 ${
                !message.trim() || isLoading
                  ? "text-gray-500 cursor-not-allowed"
                  : "text-blue-400 hover:text-blue-300"
              }`}
            />
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
