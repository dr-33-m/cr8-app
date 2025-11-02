import { Button } from "@/components/ui/button";
import {
  Play,
  Pause,
  SkipBack,
  SkipForward,
  StepBack,
  StepForward,
} from "lucide-react";
import { useAnimationControls } from "@/hooks/useAnimationControls";

export function AnimationControls() {
  const {
    animationState,
    handleFrameJumpStart,
    handleFrameJumpEnd,
    handleKeyframeJumpPrev,
    handleKeyframeJumpNext,
    handleAnimationPlay,
  } = useAnimationControls();

  return (
    <div className="flex items-center justify-center gap-1 col-span-3">
      <Button
        variant="outline"
        size="sm"
        onClick={handleFrameJumpStart}
        className="p-2"
        title="Jump to start"
      >
        <SkipBack className="h-3 w-3" />
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleKeyframeJumpPrev}
        className="p-2"
        title="Previous keyframe"
      >
        <StepBack className="h-3 w-3" />
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleAnimationPlay}
        className={`p-2 border transition-all duration-200 ${
          animationState === "playing"
            ? "bg-primary! border-primary/60! text-primary-foreground"
            : "bg-secondary! border-secondary! text-secondary-foreground hover:bg-primary/20! hover:text-primary-foreground!"
        }`}
        title={animationState === "playing" ? "Pause" : "Play"}
      >
        {animationState === "playing" ? (
          <Pause className="h-3 w-3" />
        ) : (
          <Play className="h-3 w-3" />
        )}
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleKeyframeJumpNext}
        className="p-2"
        title="Next keyframe"
      >
        <StepForward className="h-3 w-3" />
      </Button>
      <Button
        variant="outline"
        size="sm"
        onClick={handleFrameJumpEnd}
        className="p-2"
        title="Jump to end"
      >
        <SkipForward className="h-3 w-3" />
      </Button>
    </div>
  );
}
