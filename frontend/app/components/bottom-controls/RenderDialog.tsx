import { useEffect, useMemo, useState } from "react";
import { Camera as CameraIcon, Sparkles } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useSceneContext } from "@/hooks/useSceneContext";
import type {
  RenderAspect,
  RenderEngine,
  RenderOptions,
  RenderResolution,
} from "@/contexts/WebSocketContext";

/**
 * Render setup dialog.
 *
 * Deliberately exposes only what a creative decides: which camera, how big,
 * what shape, and which engine. Sample counts, denoising and GPU device
 * selection are production defaults chosen in the addon — surfacing them here
 * would be four more ways to get a worse render.
 */

const RESOLUTIONS: { value: RenderResolution; label: string; longEdge: number }[] = [
  { value: "hd", label: "HD", longEdge: 1920 },
  { value: "2k", label: "2K", longEdge: 2560 },
  { value: "4k", label: "4K", longEdge: 3840 },
];

const ASPECTS: { value: RenderAspect; label: string; w: number; h: number }[] = [
  { value: "16:9", label: "16:9", w: 16, h: 9 },
  { value: "9:16", label: "9:16", w: 9, h: 16 },
  { value: "1:1", label: "1:1", w: 1, h: 1 },
  { value: "4:5", label: "4:5", w: 4, h: 5 },
  { value: "3:2", label: "3:2", w: 3, h: 2 },
];

const ENGINES: { value: RenderEngine; label: string; hint: string }[] = [
  { value: "EEVEE", label: "EEVEE", hint: "Fast — good for iterating" },
  { value: "CYCLES", label: "Cycles", hint: "Photoreal — slower" },
];

/** Mirrors profiles.compute_dimensions in the addon, so the number shown here
 * is the number Blender renders. Kept in sync by the pixel dimensions being
 * visible — a mismatch shows up immediately in the library. */
function computeDimensions(
  resolution: RenderResolution,
  aspect: RenderAspect
): [number, number] {
  const tier = RESOLUTIONS.find((r) => r.value === resolution)!.longEdge;
  const { w, h } = ASPECTS.find((a) => a.value === aspect)!;
  let width: number;
  let height: number;
  if (w >= h) {
    width = tier;
    height = Math.round((tier * h) / w);
  } else {
    height = tier;
    width = Math.round((tier * w) / h);
  }
  return [width - (width % 2), height - (height % 2)];
}

interface RenderDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onRender: (options: RenderOptions) => void;
}

export function RenderDialog({
  open,
  onOpenChange,
  onRender,
}: RenderDialogProps) {
  const { objects } = useSceneContext();

  const cameras = useMemo(
    () => objects.filter((o) => o.type === "CAMERA"),
    [objects]
  );

  const [camera, setCamera] = useState<string>("");
  const [engine, setEngine] = useState<RenderEngine>("EEVEE");
  const [resolution, setResolution] = useState<RenderResolution>("hd");
  const [aspect, setAspect] = useState<RenderAspect>("16:9");

  // Default to the scene's active camera when the dialog opens, and re-pick if
  // the selected camera has since been deleted from the scene.
  useEffect(() => {
    if (!open) return;
    const stillThere = cameras.some((c) => c.name === camera);
    if (stillThere) return;
    const active = cameras.find((c) => c.active) ?? cameras[0];
    setCamera(active?.name ?? "");
  }, [open, cameras, camera]);

  const [width, height] = computeDimensions(resolution, aspect);
  const hasCamera = cameras.length > 0;

  const submit = () => {
    onOpenChange(false);
    onRender({ camera: camera || undefined, engine, resolution, aspect });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-4 w-4" />
            Render image
          </DialogTitle>
          <DialogDescription>
            Renders the current frame and saves it to your library.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Camera</label>
            {hasCamera ? (
              <Select value={camera} onValueChange={setCamera}>
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select a camera" />
                </SelectTrigger>
                <SelectContent>
                  {cameras.map((c) => (
                    <SelectItem key={c.name} value={c.name}>
                      <span className="flex items-center gap-2">
                        <CameraIcon className="h-3.5 w-3.5" />
                        {c.name}
                      </span>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            ) : (
              <p className="text-sm text-destructive">
                This scene has no camera. Add one before rendering.
              </p>
            )}
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Quality</label>
            <div className="grid grid-cols-3 gap-2">
              {RESOLUTIONS.map((r) => (
                <Button
                  key={r.value}
                  type="button"
                  variant={resolution === r.value ? "default" : "outline"}
                  size="sm"
                  onClick={() => setResolution(r.value)}
                >
                  {r.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Aspect ratio</label>
            <div className="grid grid-cols-5 gap-2">
              {ASPECTS.map((a) => (
                <Button
                  key={a.value}
                  type="button"
                  variant={aspect === a.value ? "default" : "outline"}
                  size="sm"
                  className="px-1 text-xs"
                  onClick={() => setAspect(a.value)}
                >
                  {a.label}
                </Button>
              ))}
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="text-sm font-medium">Render engine</label>
            <div className="grid grid-cols-2 gap-2">
              {ENGINES.map((e) => (
                <Button
                  key={e.value}
                  type="button"
                  variant={engine === e.value ? "default" : "outline"}
                  className="h-auto flex-col items-start gap-0.5 py-2"
                  onClick={() => setEngine(e.value)}
                >
                  <span className="text-sm font-medium">{e.label}</span>
                  <span className="text-xs font-normal opacity-70">
                    {e.hint}
                  </span>
                </Button>
              ))}
            </div>
          </div>

          <p className="text-xs text-muted-foreground">
            Output: {width} × {height} px
            {engine === "CYCLES" && resolution === "4k" && (
              <> — a 4K Cycles render can take several minutes.</>
            )}
          </p>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={submit} disabled={!hasCamera}>
            Render
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
