import { useCallback, useEffect, useState } from "react";
import { MoreHorizontal, Save } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import useUserStore from "@/store/userStore";

/**
 * Workspace actions menu — a menu-icon button that opens a popover of actions.
 * For now the only action is Save (to cloud); more will be added here.
 *
 * A file opened from the cloud already has a target, so Save overwrites it.
 * A brand-new project has no target yet, so Save opens a "Save As" dialog to
 * name it; once named, it behaves like a normal Save. Ctrl/Cmd+S triggers the
 * primary Save (and blocks the browser's own save-page dialog). While a save is
 * in flight the whole workspace is blocked by SavingOverlay, so `isSaving`
 * (from context) gates every entry point here.
 */
export function WorkspaceActions() {
  const { saveFile, isSaving, connectionState, isFullyConnected } =
    useWebSocketContext();
  const selectedBlendObjectKey = useUserStore((s) => s.selectedBlendObjectKey);
  const selectedBlendFile = useUserStore((s) => s.selectedBlendFile);

  const [menuOpen, setMenuOpen] = useState(false);
  const [saveAsOpen, setSaveAsOpen] = useState(false);
  const [filename, setFilename] = useState("");
  const [savedAs, setSavedAs] = useState(false);

  const disabled =
    !isFullyConnected ||
    connectionState === "blender_reconnecting" ||
    isSaving;

  // A cloud target exists if we opened a cloud file, or already did a Save As
  // this session (the backend remembers the key on the session either way).
  const hasCloudTarget = !!selectedBlendObjectKey || savedAs;

  const openSaveAs = useCallback(() => {
    setMenuOpen(false);
    const base = (selectedBlendFile || "untitled").replace(/\.blend$/i, "");
    setFilename(base);
    setSaveAsOpen(true);
  }, [selectedBlendFile]);

  const handleSave = useCallback(() => {
    if (disabled) return;
    setMenuOpen(false);
    if (hasCloudTarget) {
      saveFile();
    } else {
      openSaveAs();
    }
  }, [disabled, hasCloudTarget, saveFile, openSaveAs]);

  const submitSaveAs = useCallback(async () => {
    const name = filename.trim();
    if (!name) {
      toast.error("Enter a file name");
      return;
    }
    const withExt = /\.blend$/i.test(name) ? name : `${name}.blend`;
    setSaveAsOpen(false);
    const ok = await saveFile(withExt);
    if (ok) setSavedAs(true);
  }, [filename, saveFile]);

  // Ctrl/Cmd+S → Save (and stop the browser's save-page dialog).
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "s") {
        e.preventDefault();
        if (saveAsOpen) return; // the dialog's Enter handles submit
        if (!disabled) handleSave();
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [disabled, saveAsOpen, handleSave]);

  return (
    <>
      <Popover open={menuOpen} onOpenChange={setMenuOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            size="sm"
            className="p-2"
            title="Workspace actions"
            aria-label="Workspace actions"
            disabled={!isFullyConnected || connectionState === "blender_reconnecting"}
          >
            <MoreHorizontal className="h-3 w-3" />
          </Button>
        </PopoverTrigger>
        <PopoverContent align="start" side="top" className="w-44 p-1">
          <button
            type="button"
            disabled={disabled}
            onClick={handleSave}
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground disabled:pointer-events-none disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            Save
            <span className="ml-auto text-xs tracking-widest opacity-60">
              ⌘S
            </span>
          </button>
          <button
            type="button"
            disabled={disabled}
            onClick={openSaveAs}
            className="flex w-full items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none transition-colors hover:bg-accent hover:text-accent-foreground disabled:pointer-events-none disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            Save As…
          </button>
        </PopoverContent>
      </Popover>

      <Dialog open={saveAsOpen} onOpenChange={setSaveAsOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Save project as</DialogTitle>
            <DialogDescription>
              Name your file. It will be saved to your cloud storage as a .blend.
            </DialogDescription>
          </DialogHeader>
          <div className="flex items-center gap-2">
            <Input
              autoFocus
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  submitSaveAs();
                }
              }}
              placeholder="untitled"
            />
            <span className="text-sm text-muted-foreground">.blend</span>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setSaveAsOpen(false)}>
              Cancel
            </Button>
            <Button onClick={submitSaveAs}>Save</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
