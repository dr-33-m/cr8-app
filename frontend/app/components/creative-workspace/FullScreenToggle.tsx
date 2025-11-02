import { Button } from "@/components/ui/button";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { Maximize2, Minimize2 } from "lucide-react";
import { ReactNode } from "react";

interface ControlsOverlayProps {
  children: ReactNode;
}

export function ControlsOverlay({ children }: ControlsOverlayProps) {
  const isFullscreen = useVisibilityStore((state) => state.isFullscreen);
  const toggleFullscreen = useVisibilityStore(
    (state) => state.toggleFullscreen
  );
  return (
    <div className="z-20 absolute inset-0 pointer-events-none transition-all duration-500 ease-in-out">
      <div className="pointer-events-auto">{children}</div>
      <div className="absolute bottom-4 left-4 flex space-x-2 pointer-events-auto">
        <Button
          variant="ghost"
          size="icon"
          className="cursor-pointer"
          onClick={toggleFullscreen}
        >
          {isFullscreen ? (
            <Minimize2 className="h-5 w-5" />
          ) : (
            <Maximize2 className="h-5 w-5" />
          )}
          <span className="sr-only">Toggle Fullscreen</span>
        </Button>
      </div>
    </div>
  );
}
