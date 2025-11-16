import { Button } from "@/components/ui/button";
import { Toggle } from "@/components/ui/toggle";
import { Slider } from "@/components/ui/slider";
import {
  ContextMenu,
  ContextMenuContent,
  ContextMenuTrigger,
} from "@/components/ui/context-menu";
import {
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Settings,
  ArrowUpToLine,
  ArrowDownToLine,
} from "lucide-react";
interface EnhancedDPadProps {
  onPanUp: () => void;
  onPanDown: () => void;
  onPanLeft: () => void;
  onPanRight: () => void;
  topButtonDirection: "PANUP" | "PANFORWARD";
  bottomButtonDirection: "PANDOWN" | "PANBACK";
  panAmount: number;
  onPanAmountChange: (value: number[]) => void;
  onTopButtonToggle: () => void;
  onBottomButtonToggle: () => void;
}

export function DPad({
  onPanUp,
  onPanDown,
  onPanLeft,
  onPanRight,
  topButtonDirection,
  bottomButtonDirection,
  panAmount,
  onPanAmountChange,
  onTopButtonToggle,
  onBottomButtonToggle,
}: EnhancedDPadProps) {
  return (
    <>
      {/* Top Row - Pan Up */}
      <div className="flex justify-center gap-3">
        <Button
          variant="outline"
          size="icon"
          onClick={onPanUp}
          title={`Pan ${topButtonDirection === "PANUP" ? "Up" : "Forward"}`}
        >
          {topButtonDirection === "PANUP" ? (
            <ArrowUp className="h-4 w-4" />
          ) : (
            <ArrowUpToLine className="h-4 w-4" />
          )}
        </Button>
      </div>

      {/* Middle Row - Pan Left, Center ContextMenu, Pan Right */}
      <div className="flex justify-center items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          onClick={onPanLeft}
          title="Pan Left"
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        <ContextMenu>
          <ContextMenuTrigger asChild>
            <Button
              variant="outline"
              size="icon"
              className="w-10 h-10 rounded-full"
              title="Pan Settings"
            >
              <Settings className="h-4 w-4" />
            </Button>
          </ContextMenuTrigger>
          <ContextMenuContent className="w-48">
            <div className="p-2 space-y-2">
              {/* Top Button Toggle - Icon only */}
              <div className="flex justify-center">
                <Toggle
                  pressed={topButtonDirection === "PANFORWARD"}
                  onPressedChange={onTopButtonToggle}
                  className="w-8 h-8"
                >
                  {topButtonDirection === "PANUP" ? (
                    <ArrowUp className="h-4 w-4" />
                  ) : (
                    <ArrowUpToLine className="h-4 w-4" />
                  )}
                </Toggle>
              </div>

              {/* Bottom Button Toggle - Icon only */}
              <div className="flex justify-center">
                <Toggle
                  pressed={bottomButtonDirection === "PANBACK"}
                  onPressedChange={onBottomButtonToggle}
                  className="w-8 h-8"
                >
                  {bottomButtonDirection === "PANDOWN" ? (
                    <ArrowDown className="h-4 w-4" />
                  ) : (
                    <ArrowDownToLine className="h-4 w-4" />
                  )}
                </Toggle>
              </div>

              {/* Pan Amount Slider */}
              <div className="space-y-2 pt-2 border-t border-border">
                <div className="text-xs text-muted-foreground text-center">
                  Pan Amount: {panAmount.toFixed(1)}
                </div>
                <Slider
                  value={[panAmount]}
                  onValueChange={onPanAmountChange}
                  max={2.0}
                  min={0.1}
                  step={0.1}
                  className="w-full"
                />
              </div>
            </div>
          </ContextMenuContent>
        </ContextMenu>
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
          title={`Pan ${bottomButtonDirection === "PANDOWN" ? "Down" : "Backward"}`}
        >
          {bottomButtonDirection === "PANDOWN" ? (
            <ArrowDown className="h-4 w-4" />
          ) : (
            <ArrowDownToLine className="h-4 w-4" />
          )}
        </Button>
      </div>
    </>
  );
}
