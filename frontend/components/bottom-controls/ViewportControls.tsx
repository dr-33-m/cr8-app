import { Button } from "@/components/ui/button";
import { Eye, Monitor } from "lucide-react";
import { useNavigationControls } from "@/hooks/useNavigationControls";

export function ViewportControls() {
  const { viewportMode, handleViewportSolid, handleViewportRendered } =
    useNavigationControls();

  return (
    <div className="flex items-center gap-2">
      <Button
        variant="ghost"
        size="sm"
        onClick={handleViewportSolid}
        className={`px-3 py-2 text-xs backdrop-blur-md border transition-all duration-200 ${
          viewportMode === "solid"
            ? "bg-primary/30 border-primary/80"
            : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
        }`}
      >
        <Eye className="h-3 w-3 mr-1" />
        Solid
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleViewportRendered}
        className={`px-3 py-2 text-xs backdrop-blur-md border transition-all duration-200 ${
          viewportMode === "rendered"
            ? "bg-primary/30 border-primary/80"
            : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
        }`}
      >
        <Monitor className="h-3 w-3 mr-1" />
        Rendered
      </Button>
    </div>
  );
}
