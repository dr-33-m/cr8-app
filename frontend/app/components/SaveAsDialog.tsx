import { useEffect, useState } from "react";
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

interface SaveAsDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  /** Seed for the input, without the .blend extension. */
  defaultName?: string;
  /** Called with the name including its .blend extension. */
  onSubmit: (filename: string) => void;
  description?: string;
  submitLabel?: string;
}

/**
 * Name-this-project dialog, shared by every path that needs a cloud target:
 * the Save/Save As menu, a render with nowhere to file its output, and exiting
 * a project that has never been saved. One component so those paths cannot
 * drift apart on naming rules or copy.
 */
export function SaveAsDialog({
  open,
  onOpenChange,
  defaultName,
  onSubmit,
  description = "Name your file. It will be saved to your cloud storage as a .blend.",
  submitLabel = "Save",
}: SaveAsDialogProps) {
  const [filename, setFilename] = useState("");

  // Reseed on each open — the caller's default can change between openings
  // (e.g. after a project switch), and a stale name is worse than an empty one.
  useEffect(() => {
    if (open) setFilename((defaultName || "untitled").replace(/\.blend$/i, ""));
  }, [open, defaultName]);

  const submit = () => {
    const name = filename.trim();
    if (!name) {
      toast.error("Enter a file name");
      return;
    }
    onOpenChange(false);
    onSubmit(/\.blend$/i.test(name) ? name : `${name}.blend`);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Save project as</DialogTitle>
          <DialogDescription>{description}</DialogDescription>
        </DialogHeader>
        <div className="flex items-center gap-2">
          <Input
            autoFocus
            value={filename}
            onChange={(e) => setFilename(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") {
                e.preventDefault();
                submit();
              }
            }}
            placeholder="untitled"
          />
          <span className="text-sm text-muted-foreground">.blend</span>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={submit}>{submitLabel}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
