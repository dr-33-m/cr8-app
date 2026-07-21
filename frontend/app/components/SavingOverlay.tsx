import { useEffect, useState } from "react";
import { CloudUpload } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogTitle,
} from "@/components/ui/dialog";
import { useWebSocketContext } from "@/contexts/WebSocketContext";

/**
 * Full-screen blocking modal shown while a save is in flight.
 *
 * The save runs on Blender's main thread, which freezes the viewport and would
 * drop any commands sent meanwhile. This modal's overlay eats all interaction
 * until the save resolves. Non-dismissable by design.
 */
export function SavingOverlay() {
  const { isSaving } = useWebSocketContext();
  const [slow, setSlow] = useState(false);

  // If a save runs unusually long, point the user at the reliable escape hatch
  // (a refresh) rather than leaving them staring at an indefinite spinner.
  useEffect(() => {
    if (!isSaving) {
      setSlow(false);
      return;
    }
    const t = setTimeout(() => setSlow(true), 45_000);
    return () => clearTimeout(t);
  }, [isSaving]);

  return (
    <Dialog open={isSaving}>
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
          Saving
          <CloudUpload className="h-5 w-5 text-primary animate-pulse" />
        </DialogTitle>
        <DialogDescription>
          Saving your project to the cloud. Please wait.
        </DialogDescription>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div
            className="h-full w-1/4 rounded-full bg-primary"
            style={{ animation: "cr8-indeterminate 1.3s ease-in-out infinite" }}
          />
        </div>
        {slow && (
          <p className="text-xs text-muted-foreground">
            Taking longer than usual. If it doesn&apos;t finish shortly, refresh
            the tab and try again.
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}
