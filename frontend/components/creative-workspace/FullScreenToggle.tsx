import { Button } from "@/components/ui/button";
import { Maximize2, Minimize2 } from "lucide-react";

interface ControlsOverlayProps {
  isFullscreen: boolean;
  toggleFullscreen: () => void;
  children: React.ReactNode;
}

export function ControlsOverlay({
  isFullscreen,
  toggleFullscreen,
  children,
}: ControlsOverlayProps) {
  return (
    <div className="z-20 absolute inset-0 transition-all duration-500 ease-in-out">
      {children}
      {/* Controls Toggle Button */}
      <div className="absolute bottom-4 left-4 flex space-x-2">
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/10 backdrop-blur-sm cursor-pointer"
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
