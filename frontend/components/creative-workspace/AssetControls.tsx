import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { useAssetPlacerStore } from "@/store/assetPlacerStore";
import { useAssetPlacer } from "@/hooks/useAssetPlacer";

interface AssetControlsProps {
  assetId: string;
}

export function AssetControls({ assetId }: AssetControlsProps) {
  const placedAsset = useAssetPlacerStore((state) =>
    state.placedAssets.find((a) => a.assetId === assetId)
  );
  const { rotateAsset, scaleAsset, removeAsset } = useAssetPlacer();

  const [rotation, setRotation] = useState(placedAsset?.rotation || 0);
  const [scale, setScale] = useState(placedAsset?.scale || 100);

  // Update local state when placedAsset changes
  useEffect(() => {
    if (placedAsset) {
      setRotation(placedAsset.rotation || 0);
      setScale(placedAsset.scale || 100);
    }
  }, [placedAsset]);

  if (!placedAsset) return null;

  const handleRotate = (deg: number) => {
    setRotation(deg);
    rotateAsset(assetId, deg);
  };

  const handleScale = (percent: number) => {
    setScale(percent);
    scaleAsset(assetId, percent);
  };

  return (
    <div className="space-y-4">
      <p className="text-sm text-white/70">
        Position: <span className="text-white">{placedAsset.emptyName}</span>
      </p>

      <div className="space-y-2">
        <label className="text-sm font-medium text-white">Rotation</label>
        <Slider
          value={[rotation]}
          min={0}
          max={360}
          step={15}
          onValueChange={([val]) => handleRotate(val)}
          className="w-full"
        />
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-white">Size</label>
        <Slider
          value={[scale]}
          min={50}
          max={200}
          step={10}
          onValueChange={([val]) => handleScale(val)}
          className="w-full"
        />
      </div>

      <div className="grid grid-cols-2 gap-2">
        <Button
          variant="outline"
          onClick={() => removeAsset(assetId)}
          className="border-white/20 hover:bg-white/10"
        >
          Remove
        </Button>
        <Button className="bg-[#0077B6] hover:bg-[#0077B6]/80">Replace</Button>
      </div>
    </div>
  );
}
