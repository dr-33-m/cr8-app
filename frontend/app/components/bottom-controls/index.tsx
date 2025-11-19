import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { ChevronDown, ChevronUp, Loader2 } from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { ConnectionStatus } from "../ConnectionStatus";
import { ViewportControls } from "./ViewportControls";
import { BlazeChat } from "./blaze-chat";
import { AnimationControls } from "./AnimationControls";
import { Navigation } from "./Navigation/Navigation";
import { BottomControlsProps } from "@/lib/types/bottomControls";

export function BottomControls({ children }: BottomControlsProps) {
  const isVisible = useVisibilityStore(
    (state) => state.isBottomControlsVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleBottomControls
  );

  const {
    status,
    reconnect,
    isFullyConnected,
    connectionState,
    isHealthCheckInProgress,
  } = useWebSocketContext();

  return (
    <div
      className={`absolute bottom-4 left-1/2 transform -translate-x-1/2 transition-all duration-300 
      ${isVisible ? "translate-y-0" : "translate-y-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute left-1/2 -top-12 -translate-x-1/2"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronDown className="h-6 w-6" />
        ) : (
          <ChevronUp className="h-6 w-6" />
        )}
      </Button>

      <Card className="p-4">
        <div className="grid grid-cols-[auto_1fr_auto] grid-rows-[auto_auto_auto] gap-4 min-w-[500px]">
          {connectionState === "server_unavailable" ? (
            <div className="col-span-3 row-span-3 flex items-center justify-center flex-col gap-3">
              <div className="text-center">
                <p className="text-destructive font-medium text-sm">
                  Server Unavailable
                </p>
                <p className="text-muted-foreground text-xs mt-1">
                  Server has been down for 5+ minutes. Session cleared.
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={reconnect}
                disabled={isHealthCheckInProgress}
              >
                {isHealthCheckInProgress ? "Reconnecting" : "Reconnect"}
                {isHealthCheckInProgress && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
              </Button>
            </div>
          ) : connectionState === "disconnected" ? (
            <div className="col-span-3 row-span-3 flex items-center justify-center flex-col gap-3">
              <div className="text-center">
                <p className="text-muted-foreground font-medium text-sm">
                  Cannot connect to server
                </p>
                <p className="text-muted-foreground text-xs mt-1">
                  Please check if Cr8 Engine is running
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={reconnect}
                disabled={isHealthCheckInProgress}
              >
                {isHealthCheckInProgress ? "Reconnecting" : "Reconnect"}
                {isHealthCheckInProgress && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
              </Button>
            </div>
          ) : connectionState === "blender_disconnected" ? (
            <div className="col-span-3 row-span-3 flex items-center justify-center flex-col gap-3">
              <div className="text-center">
                <p className="text-muted-foreground font-medium text-sm">
                  Blender disconnected
                </p>
                <p className="text-muted-foreground text-xs mt-1">
                  Blender was closed or crashed
                </p>
              </div>
              <Button
                variant="secondary"
                onClick={reconnect}
                disabled={isHealthCheckInProgress}
              >
                {isHealthCheckInProgress
                  ? "Reconnecting to Blender"
                  : "Reconnect to Blender"}
                {isHealthCheckInProgress && (
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                )}
              </Button>
            </div>
          ) : connectionState === "reconnecting" ? (
            <div className="col-span-3 row-span-3 flex items-center justify-center">
              <p className="text-muted-foreground text-sm">Reconnecting...</p>
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
              <BlazeChat />

              {/* Row 3: Animation Controls - Spans all 3 columns */}
              <AnimationControls />
            </>
          ) : (
            <div className="col-span-3 row-span-3 flex items-center justify-center flex-col gap-2">
              <p className="text-muted-foreground text-sm">
                Waiting for Blender to connect...
              </p>
              <p className="text-muted-foreground text-xs">
                Please launch Blender and open your project
              </p>
            </div>
          )}
        </div>
      </Card>

      {/* Separate 3D Navigation Panel - Positioned to the right */}
      {isFullyConnected && (
        <div
          className={`absolute bottom-0 left-[calc(50%+280px)] transition-all duration-300 
    ${isVisible ? "translate-y-0" : "translate-y-full"}`}
        >
          <Navigation />
        </div>
      )}
    </div>
  );
}
