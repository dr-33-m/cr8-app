import { Boxes } from "lucide-react";
import { useAssetPlacerStore } from "@/store/assetPlacerStore";

interface AssetControlsProps {
  assetId: string;
}

export function AssetControls({ assetId }: AssetControlsProps) {
  const placedAsset = useAssetPlacerStore((state) =>
    state.placedAssets.find((a) => a.assetId === assetId)
  );

  if (!placedAsset) return null;

  return (
    <div className="space-y-4">
      <p className="text-sm text-white/70">
        Position: <span className="text-white">{placedAsset.emptyName}</span>
      </p>

      <div className="text-center text-white/60 py-6 space-y-4">
        <div className="text-4xl mb-4">
          <Boxes className="h-12 w-12 mx-auto text-purple-400" />
        </div>
        <div>
          <p className="text-base font-medium text-white">
            AI-Powered Asset Controls
          </p>
          <p className="text-sm mt-2">Control this asset using B.L.A.Z.E AI</p>
        </div>
        <div className="bg-purple-500/20 border border-purple-500/30 rounded-lg p-3 mt-4">
          <p className="text-xs text-purple-200">
            💡 Use the chat interface below to control assets with natural
            language
          </p>
        </div>
        <div className="bg-purple-500/10 border border-purple-500/20 rounded-lg p-2 mt-3">
          <p className="text-xs text-purple-300">
            🎯 Try: "Rotate this asset 45 degrees" or "Make it 50% bigger"
          </p>
        </div>
      </div>
    </div>
  );
}
