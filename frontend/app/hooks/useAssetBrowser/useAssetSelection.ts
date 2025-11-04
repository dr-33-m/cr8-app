import { useState, useCallback } from "react";
import {
  PolyHavenAsset,
  SelectionState,
  SelectionOptions,
} from "@/lib/types/assetBrowser";

export function useAssetSelection(options: SelectionOptions = {}) {
  const { onAssetSelect } = options;

  const [state, setState] = useState<SelectionState>({
    selectedAsset: null,
  });

  const selectAsset = useCallback(
    (asset: PolyHavenAsset & { id: string }) => {
      setState({ selectedAsset: asset });
      onAssetSelect?.(asset);
    },
    [onAssetSelect]
  );

  const clearSelection = useCallback(() => {
    setState({ selectedAsset: null });
  }, []);

  return {
    ...state,
    selectAsset,
    clearSelection,
  };
}
