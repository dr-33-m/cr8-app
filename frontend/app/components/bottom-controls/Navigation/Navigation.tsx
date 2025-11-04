import { Card } from "@/components/ui/card";
import { useNavigationControls } from "@/hooks/useNavigationControls";
import { Zoom } from "./Zoom";
import { Orbit } from "./Orbit";
import { DPad } from "./DPad";

export function Navigation() {
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
        {/* Cross-shaped DPad Controls */}
        <DPad
          onPanUp={handlePanUp}
          onPanDown={handlePanDown}
          onPanLeft={handlePanLeft}
          onPanRight={handlePanRight}
        />
        <div className="flex items-center justify-between gap-6">
          {/* Vertical Zoom Controls */}
          <Zoom onZoomIn={handleZoomIn} onZoomOut={handleZoomOut} />

          {/* Orbit Control */}
          <Orbit
            onOrbitUp={handleOrbitUp}
            onOrbitDown={handleOrbitDown}
            onOrbitLeft={handleOrbitLeft}
            onOrbitRight={handleOrbitRight}
          />
        </div>
      </div>
    </Card>
  );
}
