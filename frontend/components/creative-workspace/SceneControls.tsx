import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Eye,
  EyeOff,
  ScanEye,
  Move3D,
  Lightbulb,
  Triangle,
  Video,
} from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import useSceneContextStore from "@/store/sceneContextStore";
import { TransformationPopover } from "@/components/creative-workspace/TransformationPopover";

export function SceneControls() {
  const isVisible = useVisibilityStore((state) => state.isSceneControlsVisible);
  const toggleVisibility = useVisibilityStore(
    (state) => state.toggleSceneControls
  );
  const { objects, timestamp } = useSceneContextStore();

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
      <div className="backdrop-blur-md bg-white/5 rounded-lg p-6 w-80 max-h-[80vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4 text-white">Scene Objects</h2>

        {objects.length === 0 ? (
          <div className="text-center text-white/60 py-8 space-y-4">
            <div className="text-6xl mb-4">
              <Sparkles className="h-16 w-16 mx-auto text-blue-400" />
            </div>
            <div>
              <p className="text-lg font-medium text-white">No Objects</p>
              <p className="text-sm mt-2">Scene is currently empty</p>
            </div>
            <div className="bg-blue-500/20 border border-blue-500/30 rounded-lg p-3 mt-4">
              <p className="text-xs text-blue-200">
                💡 Use B.L.A.Z.E to add objects to your scene
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-3">
            <div className="text-xs text-white/60 mb-2">
              {objects.length} object{objects.length !== 1 ? "s" : ""} in scene
              {timestamp > 0 && (
                <span className="block text-[10px] mt-1">
                  Updated: {new Date(timestamp * 1000).toLocaleTimeString()}
                </span>
              )}
            </div>

            <div className="space-y-2 max-h-96 overflow-y-auto">
              {objects.map((obj, index) => (
                <div
                  key={`${obj.name}-${index}`}
                  className={`flex items-center justify-between p-3 rounded-md transition-colors ${
                    obj.active
                      ? "bg-primary/30 border border-primary/80"
                      : "bg-white/5 hover:bg-white/10"
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0 flex-1">
                    <div className="flex-shrink-0">
                      {obj.type.toLowerCase() === "light" ? (
                        <Lightbulb className="h-4 w-4 text-yellow-400" />
                      ) : obj.type.toLowerCase() === "mesh" ? (
                        <Triangle className="h-4 w-4 text-blue-400" />
                      ) : obj.type.toLowerCase() === "camera" ? (
                        <Video className="h-4 w-4 text-green-400" />
                      ) : (
                        <Triangle className="h-4 w-4 text-gray-400" />
                      )}
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="text-sm font-medium text-white truncate">
                        {obj.name}
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-1 ml-2">
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-white/60 hover:text-white hover:bg-white/10"
                    >
                      {obj.visible ? (
                        <Eye className="h-3 w-3" />
                      ) : (
                        <EyeOff className="h-3 w-3" />
                      )}
                    </Button>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 text-white/60 hover:text-white hover:bg-white/10"
                    >
                      <ScanEye className="h-3 w-3" />
                    </Button>
                    <TransformationPopover objectName={obj.name} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
