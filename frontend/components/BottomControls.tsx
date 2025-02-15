import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { ConnectionStatus } from "./ConnectionStatus";
import { useMatchRoute } from "@tanstack/react-router";
import { isEmpty } from "lodash";
import { useEffect, useState } from "react";

interface BottomControlsProps {
  children?: React.ReactNode;
}

export function BottomControls({ children }: BottomControlsProps) {
  const matchRoute = useMatchRoute();
  const [isMoodboardRoute, setMoodboardRoute] = useState(false);
  const isVisible = useVisibilityStore(
    (state) => state.isBottomControlsVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleBottomControls
  );
  const { status, reconnect } = useWebSocketContext();

  useEffect(() => {
    if (matchRoute({ to: "/project/moodboard/$moodboardId" })) {
      setMoodboardRoute(true);
    } else {
      setMoodboardRoute(false);
    }
  });

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
        {!isMoodboardRoute && (
          <>
            <ConnectionStatus status={status} />
            <div className="h-8 w-px bg-white/20" />
          </>
        )}
        {status === "disconnected" && !isMoodboardRoute ? (
          <Button
            variant="secondary"
            onClick={reconnect}
            className="bg-blue-500 hover:bg-blue-600 text-white"
          >
            Reconnect
          </Button>
        ) : (
          children
        )}
      </div>
    </div>
  );
}
