import { Button } from "@/components/ui/button";
import { ChevronDown, ChevronUp } from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { ConnectionStatus } from "../ConnectionStatus";
import { ViewportControls } from "./ViewportControls";
import { ChatInterface } from "./ChatInterface";
import { AnimationControls } from "./AnimationControls";
import { Navigation3DPanel } from "./Navigation3DPanel";

interface BottomControlsProps {
  children?: React.ReactNode;
}

export function BottomControls({ children }: BottomControlsProps) {
  const isVisible = useVisibilityStore(
    (state) => state.isBottomControlsVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleBottomControls
  );

  const { status, reconnect, isFullyConnected } = useWebSocketContext();

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

      <div className="backdrop-blur-md bg-white/5 rounded-lg p-4 grid grid-cols-[auto_1fr_auto] grid-rows-[auto_auto_auto] gap-4 min-w-[500px]">
        {status === "disconnected" ? (
          <div className="col-span-3 row-span-3 flex items-center justify-center">
            <Button
              variant="secondary"
              onClick={reconnect}
              className="bg-blue-500 hover:bg-blue-600 text-white"
            >
              Reconnect
            </Button>
          </div>
        ) : isFullyConnected ? (
          <>
            {/* Row 1 Left: Viewport Controls */}
            <ViewportControls />

            {/* Row 1 Center: Empty */}
            <div></div>

            {/* Row 1 Right: Connection Status */}
            <div className="flex items-center justify-end">
              <ConnectionStatus status={status} />
            </div>

            {/* Row 2: Chat Interface - Spans all 3 columns */}
            <ChatInterface />

            {/* Row 3: Animation Controls - Spans all 3 columns */}
            <AnimationControls />
          </>
        ) : (
          <div className="col-span-3 row-span-3 flex items-center justify-center text-white/60 text-sm">
            Waiting for Blender connection...
          </div>
        )}
      </div>

      {/* Separate 3D Navigation Panel - Positioned to the right */}
      {isFullyConnected && (
        <div
          className={`absolute bottom-0 left-[calc(50%+280px)] transition-all duration-300 
    ${isVisible ? "translate-y-0" : "translate-y-full"}`}
        >
          <Navigation3DPanel />
        </div>
      )}
    </div>
  );
}
