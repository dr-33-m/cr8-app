import { useCallback, useState } from "react";
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
import { SaveAsDialog } from "@/components/SaveAsDialog";
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
 *
 * A project that has never been saved has nowhere to save *to*, so "Save & exit"
 * collects a name first. Leaving without one is offered explicitly rather than
 * happening by default: the instance is ephemeral, so an unsaved exit is a
 * discard, and the user has to say so.
 */
export function ExitWorkspace() {
  const { saveFile, exitWorkspace, isFullyConnected, hasCloudTarget } =
    useWebSocketContext();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const selectedBlendFile = useUserStore((s) => s.selectedBlendFile);
  const clearBlendSelection = useUserStore((s) => s.clearBlendSelection);
  const setEmptyProject = useUserStore((s) => s.setEmptyProject);

  const [open, setOpen] = useState(false);
  const [saveAsOpen, setSaveAsOpen] = useState(false);

  // Teardown is identical however we leave; only whether we saved first differs.
  const leave = useCallback(() => {
    // Shut Blender/instance down on the backend (this also ends the stream).
    exitWorkspace();

    // Clear local state so home starts fresh and no stale scene/stream lingers.
    useLaunchTimerStore.getState().stop();
    queryClient.setQueryData(sceneContextKeys.objects(), null);
    useInboxStore.getState().clearAll();
    clearBlendSelection();
    setEmptyProject(false);

    navigate({ to: "/" });
  }, [
    exitWorkspace,
    queryClient,
    clearBlendSelection,
    setEmptyProject,
    navigate,
  ]);

  const handleSaveAndExit = useCallback(async () => {
    setOpen(false);

    // Never saved anywhere yet — collect a name, then exit from there.
    if (!hasCloudTarget) {
      setSaveAsOpen(true);
      return;
    }

    // If the save fails, stay put rather than silently leaving unsaved work
    // behind. saveFile has already toasted the reason.
    const ok = await saveFile();
    if (!ok) return;

    leave();
  }, [hasCloudTarget, saveFile, leave]);

  const handleSaveAsExit = useCallback(
    async (filename: string) => {
      const ok = await saveFile(filename);
      if (ok) leave();
    },
    [saveFile, leave]
  );

  const handleDiscardAndExit = useCallback(() => {
    setOpen(false);
    leave();
  }, [leave]);

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
              {hasCloudTarget
                ? "We'll save your project and shut Blender down before you go."
                : "This project has never been saved. Name it to keep it in your library — leaving without a name discards it, since the instance shuts down with you."}
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:justify-between">
            <Button variant="ghost" onClick={() => setOpen(false)}>
              Cancel
            </Button>
            <div className="flex flex-col gap-2 sm:flex-row">
              <Button variant="outline" onClick={handleDiscardAndExit}>
                {hasCloudTarget ? "Exit without saving" : "Discard & exit"}
              </Button>
              <Button onClick={handleSaveAndExit} disabled={!isFullyConnected}>
                {hasCloudTarget ? "Save & exit" : "Name, save & exit"}
              </Button>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancelling here drops back to the workspace with the work intact —
          the exit dialog is already closed, so nothing is lost by backing out. */}
      <SaveAsDialog
        open={saveAsOpen}
        onOpenChange={setSaveAsOpen}
        defaultName={selectedBlendFile}
        onSubmit={handleSaveAsExit}
        description="Name your file before you go. It will be saved to your cloud storage as a .blend."
        submitLabel="Save & exit"
      />
    </>
  );
}
