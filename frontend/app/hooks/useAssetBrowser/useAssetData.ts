import { useState, useCallback, useEffect } from "react";
import { polyhavenService } from "@/lib/services/polyhavenService";
import {
  AssetType,
  PolyHavenAsset,
  AssetDataState,
  AssetDataOptions,
} from "@/lib/types/assetBrowser";

export function useAssetData(options: AssetDataOptions = {}) {
  const {
    assetType,
    categories,
    page = 1,
    limit = 20,
    search,
    enabled = true,
  } = options;

  const [state, setState] = useState<AssetDataState>({
    assets: [],
    totalCount: 0,
    loading: false,
    error: undefined,
  });

  const loadAssets = useCallback(async () => {
    if (!enabled) return;

    setState((prev) => ({ ...prev, loading: true, error: undefined }));

    try {
      const response = await polyhavenService.getAssetsPaginated({
        assetType,
        categories:
          categories && categories.length > 0 ? categories : undefined,
        page,
        limit,
        search: search?.trim() || undefined,
      });

      const assetArray = polyhavenService.convertAssetsToArray(response.assets);

      setState({
        assets: assetArray,
        totalCount: response.pagination.total_count,
        loading: false,
        error: undefined,
      });
    } catch (err) {
      const errorMessage =
        err instanceof Error ? err.message : "Failed to load assets";
      setState({
        assets: [],
        totalCount: 0,
        loading: false,
        error: errorMessage,
      });
    }
  }, [assetType, categories, page, limit, search, enabled]);

  const refresh = useCallback(() => {
    loadAssets();
  }, [loadAssets]);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: undefined }));
  }, []);

  // Auto-load when dependencies change
  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  return {
    ...state,
    refresh,
    clearError,
  };
}
