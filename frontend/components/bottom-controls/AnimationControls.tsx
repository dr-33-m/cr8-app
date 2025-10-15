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
        variant="ghost"
        size="sm"
        onClick={handleFrameJumpStart}
        className="p-2 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
        title="Jump to start"
      >
        <SkipBack className="h-3 w-3" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleKeyframeJumpPrev}
        className="p-2 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
        title="Previous keyframe"
      >
        <StepBack className="h-3 w-3" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleAnimationPlay}
        className={`p-2 border transition-all duration-200 ${
          animationState === "playing"
            ? "bg-green-500/20 border-green-400/40 text-green-300"
            : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
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
        variant="ghost"
        size="sm"
        onClick={handleKeyframeJumpNext}
        className="p-2 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
        title="Next keyframe"
      >
        <StepForward className="h-3 w-3" />
      </Button>
      <Button
        variant="ghost"
        size="sm"
        onClick={handleFrameJumpEnd}
        className="p-2 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
        title="Jump to end"
      >
        <SkipForward className="h-3 w-3" />
      </Button>
    </div>
  );
}
