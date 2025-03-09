import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAssetPlacerStore } from "@/store/assetPlacerStore";
import { useAssetPlacer } from "@/hooks/useAssetPlacer";

export function SwapAssetsControl() {
  const [selectedAsset1, setSelectedAsset1] = useState<string | null>(null);
  const [selectedAsset2, setSelectedAsset2] = useState<string | null>(null);

  // Get store data at component level
  const placedAssets = useAssetPlacerStore((state) => state.placedAssets);
  const availableAssets = useAssetPlacerStore((state) => state.availableAssets);
  const { swapAssets } = useAssetPlacer();

  // Memoize the asset name lookup function
  const getAssetName = useMemo(() => {
    return (assetId: string) => {
      return (
        availableAssets.find((a) => a.id === assetId)?.name || "Unknown Asset"
      );
    };
  }, [availableAssets]);

  // Memoize the filtered assets for the second dropdown
  const filteredAssets = useMemo(() => {
    if (!selectedAsset1) return [];
    return placedAssets.filter((asset) => asset.assetId !== selectedAsset1);
  }, [placedAssets, selectedAsset1]);

  return (
    <div className="backdrop-blur-md bg-white/5 p-4 rounded-lg space-y-4">
      <h3 className="font-medium text-white">Swap Assets</h3>

      <div className="space-y-2">
        <label className="text-sm font-medium text-white">First Asset</label>
        <Select onValueChange={(value) => setSelectedAsset1(value)}>
          <SelectTrigger className="bg-white/10 border-white/20">
            <SelectValue placeholder="Select first asset" />
          </SelectTrigger>
          <SelectContent className="bg-[#1C1C1C] border-white/20">
            {placedAssets.map((asset) => (
              <SelectItem key={asset.assetId} value={asset.assetId}>
                {getAssetName(asset.assetId)} ({asset.emptyName})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-2">
        <label className="text-sm font-medium text-white">Second Asset</label>
        <Select
          onValueChange={(value) => setSelectedAsset2(value)}
          disabled={!selectedAsset1}
        >
          <SelectTrigger className="bg-white/10 border-white/20">
            <SelectValue placeholder="Select second asset" />
          </SelectTrigger>
          <SelectContent className="bg-[#1C1C1C] border-white/20">
            {filteredAssets.map((asset) => (
              <SelectItem key={asset.assetId} value={asset.assetId}>
                {getAssetName(asset.assetId)} ({asset.emptyName})
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Button
        className="w-full"
        disabled={!selectedAsset1 || !selectedAsset2}
        onClick={() => {
          if (selectedAsset1 && selectedAsset2) {
            swapAssets(selectedAsset1, selectedAsset2);
            setSelectedAsset1(null);
            setSelectedAsset2(null);
          }
        }}
      >
        Swap Assets
      </Button>
    </div>
  );
}
