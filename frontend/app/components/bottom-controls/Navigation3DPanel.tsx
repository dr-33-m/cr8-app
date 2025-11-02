import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
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
    <Card className="p-3">
      <div className="flex flex-col gap-3">
        {/* Top Row - Zoom In and Pan Up */}
        <div className="flex justify-center gap-3">
          <Button
            variant="outline"
            size="icon"
            onClick={handleZoomIn}
            title="Zoom In"
          >
            <Plus className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={handlePanUp}
            title="Pan Up"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>
        </div>

        {/* Middle Row - Pan Left, Center Space, Pan Right */}
        <div className="flex justify-center items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            onClick={handlePanLeft}
            title="Pan Left"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          <div className="w-10 h-10"></div>
          <Button
            variant="outline"
            size="icon"
            onClick={handlePanRight}
            title="Pan Right"
          >
            <ArrowRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Bottom Row - Zoom Out, Pan Down, and Orbit Control */}
        <div className="flex justify-center items-center gap-3">
          <Button
            variant="outline"
            size="icon"
            onClick={handleZoomOut}
            title="Zoom Out"
          >
            <Minus className="h-4 w-4" />
          </Button>
          <Button
            variant="outline"
            size="icon"
            onClick={handlePanDown}
            title="Pan Down"
          >
            <ArrowDown className="h-4 w-4" />
          </Button>

          {/* Orbit Control Wheel */}
          <div className="w-16 h-16 relative flex items-center justify-center">
            <div className="w-16 h-16 bg-secondary/30 border border-border rounded-full relative overflow-hidden shadow-sm">
              {/* Top Quarter - Orbit Up */}
              <Button
                variant="ghost"
                size="icon"
                onClick={handleOrbitUp}
                className="absolute top-0 left-1/2 transform -translate-x-1/2 w-8 h-8 rounded-t-full p-0 hover:bg-primary/30! transition-colors"
                title="Orbit Up"
              >
                <ArrowUp className="h-4 w-4" />
              </Button>

              {/* Right Quarter - Orbit Right */}
              <Button
                variant="ghost"
                size="icon"
                onClick={handleOrbitRight}
                className="absolute right-0 top-1/2 transform -translate-y-1/2 w-8 h-8 rounded-r-full p-0 hover:bg-primary/30! transition-colors"
                title="Orbit Right"
              >
                <ArrowRight className="h-4 w-4" />
              </Button>

              {/* Bottom Quarter - Orbit Down */}
              <Button
                variant="ghost"
                size="icon"
                onClick={handleOrbitDown}
                className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-8 rounded-b-full p-0 hover:bg-primary/30! transition-colors"
                title="Orbit Down"
              >
                <ArrowDown className="h-4 w-4" />
              </Button>

              {/* Left Quarter - Orbit Left */}
              <Button
                variant="ghost"
                size="icon"
                onClick={handleOrbitLeft}
                className="absolute left-0 top-1/2 transform -translate-y-1/2 w-8 h-8 rounded-l-full p-0 hover:bg-primary/30! transition-colors"
                title="Orbit Left"
              >
                <ArrowLeft className="h-4 w-4" />
              </Button>

              {/* Center Circle */}
              <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-primary/20 border border-primary/30 rounded-full shadow-sm"></div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
}
