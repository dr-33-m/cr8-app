import { useState } from "react";
import { PolyHavenAsset, SelectionOptions } from "@/lib/types/assetBrowser";

export function useAssetSelection(options: SelectionOptions = {}) {
  const { onAssetSelect } = options;

  const [selectedAsset, setSelectedAsset] = useState<
    (PolyHavenAsset & { id: string }) | null
  >(null);

  const selectAsset = (asset: PolyHavenAsset & { id: string }) => {
    setSelectedAsset(asset);
    onAssetSelect?.(asset);
  };

  const clearSelection = () => {
    setSelectedAsset(null);
  };

  return {
    selectedAsset,
    selectAsset,
    clearSelection,
  };
}
