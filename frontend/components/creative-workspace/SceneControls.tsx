import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Sparkles } from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";

export function SceneControls() {
  const isVisible = useVisibilityStore((state) => state.isSceneControlsVisible);
  const toggleVisibility = useVisibilityStore(
    (state) => state.toggleSceneControls
  );

  return (
    <div
      className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 
      ${isVisible ? "translate-x-0" : "-translate-x-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-12 top-0 text-white hover:bg-white/10"
        onClick={toggleVisibility}
      >
        {isVisible ? (
          <ChevronLeft className="h-6 w-6" />
        ) : (
          <ChevronRight className="h-6 w-6" />
        )}
      </Button>
      <div className="backdrop-blur-md bg-white/5 rounded-lg p-6 w-80">
        <h2 className="text-xl font-semibold mb-4 text-white">
          Scene Controls
        </h2>
        <div className="text-center text-white/60 py-8 space-y-4">
          <div className="text-6xl mb-4">
            <Sparkles className="h-16 w-16 mx-auto text-blue-400" />
          </div>
          <div>
            <p className="text-lg font-medium text-white">Coming Soon</p>
            <p className="text-sm mt-2">
              Advanced scene controls powered by B.L.A.Z.E
            </p>
          </div>
          <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-3 mt-4">
            <p className="text-xs text-blue-200">
              💡 Use the chat interface below to control your scene with natural
              language
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
