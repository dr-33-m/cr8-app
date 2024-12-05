import { Button } from "@/components/ui/button";
import {
  Play,
  ChevronLeft,
  ChevronRight,
  RotateCcw,
  ZoomIn,
  Move,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

interface BottomControlsProps {
  isVisible: boolean;
  isFullscreen: boolean;
  onToggleVisibility: () => void;
  onStreamViewport: () => void;
}

export function BottomControls({
  isVisible,
  isFullscreen,
  onToggleVisibility,
  onStreamViewport,
}: BottomControlsProps) {
  return (
    <div
      className={`absolute bottom-4 left-1/2 transform -translate-x-1/2 transition-all duration-300 
      ${isVisible ? "translate-y-0" : "translate-y-full"}
      ${isFullscreen ? "scale-75" : ""}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute left-1/2 -top-12 -translate-x-1/2 text-white hover:bg-white/10"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronDown className="h-6 w-6" />
        ) : (
          <ChevronUp className="h-6 w-6" />
        )}
      </Button>
      <div className="backdrop-blur-md bg-white/5 rounded-lg px-6 py-3 flex items-center space-x-6">
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/10"
          title="Previous"
        >
          <ChevronLeft className="h-6 w-6" />
          <span className="sr-only">Previous</span>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-[#FFD100] hover:bg-[#FFD100]/10"
          title="Play Preview"
          onClick={onStreamViewport}
        >
          <Play className="h-6 w-6" />
          <span className="sr-only">Play Preview</span>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/10"
          title="Next"
        >
          <ChevronRight className="h-6 w-6" />
          <span className="sr-only">Next</span>
        </Button>
        <div className="h-8 w-px bg-white/20" />
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/10"
          title="Rotate"
        >
          <RotateCcw className="h-5 w-5" />
          <span className="sr-only">Rotate</span>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/10"
          title="Zoom"
        >
          <ZoomIn className="h-5 w-5" />
          <span className="sr-only">Zoom</span>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/10"
          title="Pan"
        >
          <Move className="h-5 w-5" />
          <span className="sr-only">Pan</span>
        </Button>
      </div>
    </div>
  );
}
