import { Button } from "@/components/ui/button";
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from "lucide-react";
import { OrbitProps } from "@/lib/types/bottomControls";

export function Orbit({
  onOrbitUp,
  onOrbitDown,
  onOrbitLeft,
  onOrbitRight,
}: OrbitProps) {
  return (
    <>
      {/* Orbit Control Wheel */}
      <div className="w-16 h-16 relative flex items-center justify-center">
        <div className="w-16 h-16 bg-secondary/30 border border-border rounded-full relative overflow-hidden shadow-sm">
          {/* Top Quarter - Orbit Up */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onOrbitUp}
            className="absolute top-0 left-1/2 transform -translate-x-1/2 w-8 h-8 rounded-t-full p-0 hover:bg-primary/30! transition-colors"
            title="Orbit Up"
          >
            <ArrowUp className="h-4 w-4" />
          </Button>

          {/* Right Quarter - Orbit Right */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onOrbitRight}
            className="absolute right-0 top-1/2 transform -translate-y-1/2 w-8 h-8 rounded-r-full p-0 hover:bg-primary/30! transition-colors"
            title="Orbit Right"
          >
            <ArrowRight className="h-4 w-4" />
          </Button>

          {/* Bottom Quarter - Orbit Down */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onOrbitDown}
            className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-8 rounded-b-full p-0 hover:bg-primary/30! transition-colors"
            title="Orbit Down"
          >
            <ArrowDown className="h-4 w-4" />
          </Button>

          {/* Left Quarter - Orbit Left */}
          <Button
            variant="ghost"
            size="icon"
            onClick={onOrbitLeft}
            className="absolute left-0 top-1/2 transform -translate-y-1/2 w-8 h-8 rounded-l-full p-0 hover:bg-primary/30! transition-colors"
            title="Orbit Left"
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>

          {/* Center Circle */}
          <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-primary/20 border border-primary/30 rounded-full shadow-sm"></div>
        </div>
      </div>
    </>
  );
}
