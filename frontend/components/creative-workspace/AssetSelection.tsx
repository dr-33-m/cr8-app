import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight, Package } from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";

export function AssetSelection() {
  const isVisible = useVisibilityStore(
    (state) => state.isAssetSelectionVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleAssetSelection
  );
  return (
    <div
      className={`absolute right-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 
      ${isVisible ? "translate-x-0" : "translate-x-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -left-12 top-0 text-white hover:bg-white/10"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronRight className="h-6 w-6" />
        ) : (
          <ChevronLeft className="h-6 w-6" />
        )}
      </Button>
      <div className="backdrop-blur-md bg-white/5 rounded-lg p-6 w-80">
        <h2 className="text-xl font-semibold mb-4 text-white">
          Asset Management
        </h2>
        <div className="text-center text-white/60 py-8 space-y-4">
          <div className="text-6xl mb-4">
            <Package className="h-16 w-16 mx-auto text-orange-400" />
          </div>
          <div>
            <p className="text-lg font-medium text-white">Coming Soon</p>
            <p className="text-sm mt-2">
              Advanced asset management powered by B.L.A.Z.E
            </p>
          </div>
          <div className="bg-orange-500/20 border border-orange-500/30 rounded-lg p-3 mt-4">
            <p className="text-xs text-orange-200">
              💡 Use the chat interface below to manage assets with natural
              language
            </p>
          </div>
          <div className="bg-orange-500/10 border border-orange-500/20 rounded-lg p-2 mt-3">
            <p className="text-xs text-orange-300">
              🎯 Try: "Place the Jordan shoes on the table" or "Remove all
              assets from the scene"
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
