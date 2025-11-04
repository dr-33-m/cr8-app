import { Button } from "@/components/ui/button";
import { ArrowUp, ArrowDown, ArrowLeft, ArrowRight } from "lucide-react";

interface DPadProps {
  onPanUp: () => void;
  onPanDown: () => void;
  onPanLeft: () => void;
  onPanRight: () => void;
}

export function DPad({ onPanUp, onPanDown, onPanLeft, onPanRight }: DPadProps) {
  return (
    <>
      {/* Top Row - Pan Up */}
      <div className="flex justify-center gap-3">
        <Button variant="outline" size="icon" onClick={onPanUp} title="Pan Up">
          <ArrowUp className="h-4 w-4" />
        </Button>
      </div>

      {/* Middle Row - Pan Left, Center Space, Pan Right */}
      <div className="flex justify-center items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          onClick={onPanLeft}
          title="Pan Left"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <div className="w-10 h-10"></div>
        <Button
          variant="outline"
          size="icon"
          onClick={onPanRight}
          title="Pan Right"
        >
          <ArrowRight className="h-4 w-4" />
        </Button>
      </div>

      {/* Bottom Row - Pan Down */}
      <div className="flex justify-center items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          onClick={onPanDown}
          title="Pan Down"
        >
          <ArrowDown className="h-4 w-4" />
        </Button>
      </div>
    </>
  );
}
