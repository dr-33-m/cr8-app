import { useState, useCallback } from "react";
import { PolyHavenAsset } from "@/lib/services/polyhavenService";

export interface SelectionState {
  selectedAsset: (PolyHavenAsset & { id: string }) | null;
}

export interface SelectionOptions {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
}

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
