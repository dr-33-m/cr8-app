import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { PolyHavenPanel } from "./PolyHavenPanel";
import { PolyHavenAsset } from "@/lib/services/polyhavenService";
import { toast } from "sonner";

export function AssetSelection() {
  const isVisible = useVisibilityStore(
    (state) => state.isAssetSelectionVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleAssetSelection
  );

  const handleAssetSelect = (asset: PolyHavenAsset & { id: string }) => {
    toast.success(`Selected asset: ${asset.name}`);
    // TODO: Integrate with Blender workflow
    console.log("Selected asset:", asset);
  };

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
      <div className="backdrop-blur-md bg-white/5 rounded-lg p-6 w-80 max-h-[80vh] overflow-y-auto">
        <h2 className="text-xl font-semibold mb-4 text-white">Asset Browser</h2>
        <PolyHavenPanel onAssetSelect={handleAssetSelect} />
      </div>
    </div>
  );
}
