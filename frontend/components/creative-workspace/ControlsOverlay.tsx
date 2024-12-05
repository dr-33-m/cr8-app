import { Button } from "@/components/ui/button";
import { Menu, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface ControlsOverlayProps {
  isFullscreen: boolean;
  isControlsVisible: boolean;
  toggleControls: () => void;
  children: React.ReactNode;
}

export function ControlsOverlay({
  isFullscreen,
  isControlsVisible,
  toggleControls,
  children,
}: ControlsOverlayProps) {
  return (
    <div
      className={cn(
        "z-20 absolute inset-0",
        "transition-all duration-500 ease-in-out",
        isFullscreen
          ? "opacity-0 pointer-events-none hover:opacity-100 hover:pointer-events-auto"
          : "opacity-100",
        isFullscreen ? "bg-black/50" : ""
      )}
    >
      {children}

      {/* Controls Toggle Button */}
      <div className="absolute bottom-4 left-4 flex space-x-2">
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/10 backdrop-blur-sm"
          onClick={toggleControls}
        >
          {isControlsVisible ? (
            <X className="h-5 w-5" />
          ) : (
            <Menu className="h-5 w-5" />
          )}
          <span className="sr-only">Toggle Controls</span>
        </Button>
      </div>
    </div>
  );
}
