import { Button } from "@/components/ui/button";
import { Plus, Minus } from "lucide-react";
import { ZoomProps } from "@/lib/types/bottomControls";

export function Zoom({ onZoomIn, onZoomOut }: ZoomProps) {
  return (
    <div className="flex gap-2">
      <Button
        variant="outline"
        size="icon"
        onClick={onZoomOut}
        title="Zoom Out"
      >
        <Minus className="h-4 w-4" />
      </Button>
      <Button variant="outline" size="icon" onClick={onZoomIn} title="Zoom In">
        <Plus className="h-4 w-4" />
      </Button>
    </div>
  );
}
