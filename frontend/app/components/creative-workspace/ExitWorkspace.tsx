import { useState } from "react";
import { ArrowLeftFromLine, Sparkles } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";
import { useQueryClient } from "@tanstack/react-query";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import useUserStore from "@/store/userStore";
import useInboxStore from "@/store/inboxStore";
import { useLaunchTimerStore } from "@/store/launchTimerStore";
import { sceneContextKeys } from "@/websocket/query-manager/scene-context";

/**
 * Exit button (bottom-left) + tidy-up confirm dialog.
 *
 * Leaving the workspace should be a clean shutdown, not a background orphan:
 * save the file, shut Blender (and its stream) down, clear local state, then go
 * home. This is the only sanctioned way out — the navbar logo is disabled inside
 * the workspace so users don't strand a running instance behind them.
 */
export function ExitWorkspace() {
  const { saveFile, exitWorkspace, isFullyConnected } = useWebSocketContext();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const selectedBlendObjectKey = useUserStore((s) => s.selectedBlendObjectKey);
  const clearBlendSelection = useUserStore((s) => s.clearBlendSelection);
  const setEmptyProject = useUserStore((s) => s.setEmptyProject);

  const [open, setOpen] = useState(false);

  const handleExit = async () => {
    setOpen(false);

    // Save first if there's a cloud file to save to. If the save fails, stay put
    // rather than silently leaving unsaved work behind.
    if (isFullyConnected && selectedBlendObjectKey) {
      const ok = await saveFile();
      if (!ok) return;
    }

    // Shut Blender/instance down on the backend (this also ends the stream).
    exitWorkspace();

    // Clear local state so home starts fresh and no stale scene/stream lingers.
    useLaunchTimerStore.getState().stop();
    queryClient.setQueryData(sceneContextKeys.objects(), null);
    useInboxStore.getState().clearAll();
    clearBlendSelection();
    setEmptyProject(false);

    navigate({ to: "/" });
  };

  return (
    <>
      <div className="absolute bottom-4 left-4 z-30 pointer-events-auto">
        <Button
          variant="ghost"
          size="icon"
          className="cursor-pointer"
          title="Exit workspace"
          onClick={() => setOpen(true)}
        >
          <ArrowLeftFromLine className="h-5 w-5" />
          <span className="sr-only">Exit workspace</span>
        </Button>
      </div>

      <Dialog open={open} onOpenChange={setOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              Tidy up &amp; leave
              <Sparkles className="h-5 w-5 text-primary" />
            </DialogTitle>
            <DialogDescription>
              We&apos;ll save your project and shut Blender down before you go.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleExit}>Save &amp; exit</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
