import { Button } from "@/components/ui/button";
import {
  Plus,
  Minus,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
} from "lucide-react";
import { useNavigationControls } from "@/hooks/useNavigationControls";

export function Navigation3DPanel() {
  const {
    handleZoomIn,
    handleZoomOut,
    handlePanUp,
    handlePanDown,
    handlePanLeft,
    handlePanRight,
    handleOrbitLeft,
    handleOrbitRight,
    handleOrbitUp,
    handleOrbitDown,
  } = useNavigationControls();

  return (
    <div className="backdrop-blur-md bg-white/5 rounded-lg p-3 border border-white/10">
      <div className="flex flex-col gap-3">
        {/* Top Row - Zoom In and Pan Up */}
        <div className="flex justify-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomIn}
            className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
            title="Zoom In"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePanUp}
            className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
            title="Pan Up"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        </div>

        {/* Middle Row - Pan Left, Center Space, Pan Right */}
        <div className="flex justify-center items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePanLeft}
            className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
            title="Pan Left"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="w-10 h-10"></div>
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePanRight}
            className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
            title="Pan Right"
          >
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Bottom Row - Zoom Out, Pan Down, and Orbit Control */}
        <div className="flex justify-center items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={handleZoomOut}
            className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
            title="Zoom Out"
          >
            <Minus className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            onClick={handlePanDown}
            className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
            title="Pan Down"
          >
            <ArrowDown className="h-4 w-4" />
          </Button>

          {/* Orbit Control Wheel */}
          <div className="w-16 h-16 relative flex items-center justify-center">
            <div className="w-16 h-16 bg-black/40 border border-white/20 rounded-full relative overflow-hidden">
              {/* Top Quarter - Orbit Up */}
              <button
                onClick={handleOrbitUp}
                className="absolute top-0 left-1/2 transform -translate-x-1/2 w-8 h-8 hover:bg-white/20 rounded-t-full transition-colors flex items-center justify-center"
                title="Orbit Up"
              >
                <ArrowUp className="h-4 w-4 text-white/90" />
              </button>

              {/* Right Quarter - Orbit Right */}
              <button
                onClick={handleOrbitRight}
                className="absolute right-0 top-1/2 transform -translate-y-1/2 w-8 h-8 hover:bg-white/20 rounded-r-full transition-colors flex items-center justify-center"
                title="Orbit Right"
              >
                <ArrowRight className="h-4 w-4 text-white/90" />
              </button>

              {/* Bottom Quarter - Orbit Down */}
              <button
                onClick={handleOrbitDown}
                className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-8 hover:bg-white/20 rounded-b-full transition-colors flex items-center justify-center"
                title="Orbit Down"
              >
                <ArrowDown className="h-4 w-4 text-white/90" />
              </button>

              {/* Left Quarter - Orbit Left */}
              <button
                onClick={handleOrbitLeft}
                className="absolute left-0 top-1/2 transform -translate-y-1/2 w-8 h-8 hover:bg-white/20 rounded-l-full transition-colors flex items-center justify-center"
                title="Orbit Left"
              >
                <ArrowLeft className="h-4 w-4 text-white/90" />
              </button>

              {/* Center Circle */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-white/20 rounded-full"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
