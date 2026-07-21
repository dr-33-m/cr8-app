import { useEffect, useState } from "react";
import { Sparkles } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { formatElapsedSeconds } from "@/lib/formatters";

/**
 * Full-screen blocking modal shown while a render is in flight.
 *
 * The render occupies Blender's main thread — the viewport stream freezes and
 * no other command runs until it finishes — so this eats all interaction until
 * it resolves. Non-dismissable by design.
 *
 * The progress is an elapsed counter rather than a percentage: Blender's
 * render_stats handler is only dependable in background mode, and this Blender
 * runs with a GUI for the WebRTC stream. A bar that silently never moves would
 * be worse than an honest clock.
 */
export function RenderingOverlay() {
  const { isRendering } = useWebSocketContext();
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!isRendering) {
      setElapsed(0);
      return;
    }
    const started = Date.now();
    const id = setInterval(
      () => setElapsed(Math.floor((Date.now() - started) / 1000)),
      1000
    );
    return () => clearInterval(id);
  }, [isRendering]);

  return (
    <Dialog open={isRendering}>
      <DialogContent
        showCloseButton={false}
        onEscapeKeyDown={(e) => e.preventDefault()}
        onPointerDownOutside={(e) => e.preventDefault()}
        onInteractOutside={(e) => e.preventDefault()}
        className="sm:max-w-sm"
      >
        <style>{`
          @keyframes cr8-indeterminate {
            0% { transform: translateX(-110%); }
            100% { transform: translateX(430%); }
          }
        `}</style>
        <DialogTitle className="flex items-center gap-2">
          Rendering
          <Sparkles className="h-5 w-5 text-primary animate-pulse" />
        </DialogTitle>
        <DialogDescription>
          Blender is rendering your image. The viewport is frozen until it
          finishes — this is normal.
        </DialogDescription>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full w-1/4 rounded-full bg-primary"
            style={{ animation: "cr8-indeterminate 1.3s ease-in-out infinite" }}
          />
        </div>
        <p className="text-xs text-muted-foreground tabular-nums">
          {formatElapsedSeconds(elapsed)} elapsed
          {elapsed > 180 && " — high-resolution Cycles renders take a while"}
        </p>
      </DialogContent>
    </Dialog>
  );
}
