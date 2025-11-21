import { useQuery } from "@tanstack/react-query";
import { createAssetsPaginatedQueryOptions } from "@/server/query-manager/polyhaven";
import type {
  PolyHavenAsset,
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

  // Use React Query for server state management
  const { data, isLoading, error, refetch } = useQuery(
    createAssetsPaginatedQueryOptions(
      {
        assetType,
        categories:
          categories && categories.length > 0 ? categories : undefined,
        page,
        limit,
        search: search?.trim() || undefined,
      },
      { enabled }
    )
  );

  // Transform response to match existing interface
  const assets: Array<PolyHavenAsset & { id: string }> = data?.assets
    ? Object.entries(data.assets).map(([id, asset]) => ({
        ...asset,
        id,
      }))
    : [];

  const totalCount = data?.pagination.total_count ?? 0;

  return {
    // State
    assets,
    totalCount,
    loading: isLoading,
    error: error instanceof Error ? error.message : null,

    // Actions
    refresh: refetch,
  };
}
