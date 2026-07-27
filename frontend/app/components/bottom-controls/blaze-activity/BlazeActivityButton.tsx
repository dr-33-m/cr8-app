import { useCallback } from "react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import useBlazeChatStore from "@/store/blazeChatStore";
import { BlazeLogo } from "@/components/icons/BlazeLogo";

/**
 * B.L.A.Z.E's mark, doubling as its status light.
 *
 * It pulses in the primary colour while B.L.A.Z.E is working and sits grey when
 * idle — so a finished run is obvious without waiting on a toast that may
 * already have dismissed itself. Clicking slides the right-hand card over to the
 * chat, opening it first if it was collapsed.
 */
export function BlazeActivityButton() {
  const { isFullyConnected, connectionState } = useWebSocketContext();
  const isBusy = useBlazeChatStore((s) => s.isBusy);
  const hasUnseen = useBlazeChatStore((s) => s.hasUnseen);
  const markSeen = useBlazeChatStore((s) => s.markSeen);
  const showRightPanel = useVisibilityStore((s) => s.showRightPanel);
  const rightPanel = useVisibilityStore((s) => s.rightPanel);
  const isCardOpen = useVisibilityStore((s) => s.isAssetSelectionVisible);

  const chatShowing = isCardOpen && rightPanel === "chat";

  const handleClick = useCallback(() => {
    // Already looking at it — collapse rather than no-op.
    if (chatShowing) {
      useVisibilityStore.getState().setAssetSelectionVisible(false);
      return;
    }
    showRightPanel("chat");
    markSeen();
  }, [chatShowing, showRightPanel, markSeen]);

  const label = isBusy
    ? "B.L.A.Z.E is working — open chat"
    : chatShowing
      ? "Hide B.L.A.Z.E chat"
      : "Open B.L.A.Z.E chat";

  return (
    <Button
      variant="outline"
      size="sm"
      className="relative p-2"
      title={label}
      aria-label={label}
      disabled={!isFullyConnected || connectionState === "blender_reconnecting"}
      onClick={handleClick}
    >
      <BlazeLogo
        className={cn(
          "h-3.5 w-3.5 transition-colors",
          isBusy
            ? "animate-pulse text-primary"
            : chatShowing
              ? "text-foreground"
              : "text-muted-foreground"
        )}
      />
      {isBusy && (
        // Halo behind the mark, so the pulse still reads at this size.
        <span className="pointer-events-none absolute inset-0 animate-pulse rounded-md bg-primary/15" />
      )}
      {!isBusy && hasUnseen && (
        <span className="pointer-events-none absolute -right-0.5 -top-0.5 h-2 w-2 rounded-full bg-primary" />
      )}
    </Button>
  );
}
