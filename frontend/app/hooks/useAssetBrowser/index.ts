import { useState, useEffect } from "react";
import { AssetType, PolyHavenAsset } from "@/lib/services/polyhavenService";
import { useAssetData } from "./useAssetData";
import { useAssetSearch } from "./useAssetSearch";
import { useAssetPagination } from "./useAssetPagination";
import { useAssetCategories } from "./useAssetCategories";
import { useAssetSelection } from "./useAssetSelection";

export interface UseAssetBrowserOptions {
  initialType?: AssetType;
  initialSearch?: string;
  initialLimit?: number;
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  enabled?: boolean;
}

export function useAssetBrowser(options: UseAssetBrowserOptions = {}) {
  const {
    initialType = "textures",
    initialSearch = "",
    initialLimit = 20,
    onAssetSelect,
    enabled = true,
  } = options;

  // Asset type state (managed at this level)
  const [selectedType, setSelectedType] = useState<AssetType>(initialType);

  // Search functionality
  const search = useAssetSearch({
    initialQuery: initialSearch,
    debounceMs: 300,
  });

  // Pagination
  const pagination = useAssetPagination({
    initialPage: 1,
    initialLimit,
  });

  // Categories
  const categories = useAssetCategories({
    assetType: selectedType,
    enabled,
  });

  // Asset selection
  const selection = useAssetSelection({
    onAssetSelect,
  });

  // Asset data - depends on all other states
  const assetData = useAssetData({
    assetType: selectedType,
    categories: categories.selectedCategories,
    page: pagination.page,
    limit: pagination.limit,
    search: search.debouncedQuery,
    enabled,
  });

  // Update pagination when asset data changes
  useEffect(() => {
    if (assetData.totalCount > 0) {
      pagination.updatePagination({
        page: pagination.page,
        limit: pagination.limit,
        total_count: assetData.totalCount,
        total_pages: Math.ceil(assetData.totalCount / pagination.limit),
        has_next: pagination.page * pagination.limit < assetData.totalCount,
        has_prev: pagination.page > 1,
      });
    }
  }, [assetData.totalCount, pagination.page, pagination.limit]);

  // Reset pagination when filters change
  useEffect(() => {
    pagination.firstPage();
  }, [selectedType, search.debouncedQuery, categories.selectedCategories]);

  // Handle asset type change
  const handleTypeChange = (type: AssetType) => {
    setSelectedType(type);
    search.clearQuery();
    categories.clearCategories();
  };

  // Handle search
  const handleSearch = (query: string) => {
    search.setQuery(query);
  };

  // Handle pagination
  const handlePageChange = (page: number) => {
    pagination.setPage(page);
  };

  // Get limited assets for compact view
  const getLimitedAssets = (limit: number = 6) => {
    return assetData.assets.slice(0, limit);
  };

  return {
    // State
    selectedType,
    assets: assetData.assets,
    totalCount: assetData.totalCount,
    loading: assetData.loading || categories.loading,
    error: assetData.error || categories.error,

    // Search
    searchQuery: search.query,
    debouncedSearchQuery: search.debouncedQuery,

    // Categories
    categories: categories.categories,
    selectedCategories: categories.selectedCategories,

    // Pagination
    pagination: {
      page: pagination.page,
      limit: pagination.limit,
      totalPages: pagination.totalPages,
      hasNext: pagination.hasNext,
      hasPrev: pagination.hasPrev,
    },

    // Selection
    selectedAsset: selection.selectedAsset,

    // Actions
    setType: handleTypeChange,
    setSearch: handleSearch,
    clearSearch: search.clearQuery,

    // Category actions
    toggleCategory: categories.toggleCategory,
    addCategory: categories.addCategory,
    removeCategory: categories.removeCategory,
    setCategories: categories.setCategories,
    clearCategories: categories.clearCategories,

    // Pagination actions
    setPage: handlePageChange,
    nextPage: pagination.nextPage,
    prevPage: pagination.prevPage,
    firstPage: pagination.firstPage,
    lastPage: pagination.lastPage,

    // Selection actions
    selectAsset: selection.selectAsset,
    clearSelection: selection.clearSelection,

    // Utility actions
    refresh: assetData.refresh,
    clearError: () => {
      assetData.clearError();
      categories.clearError();
    },

    // Utility methods
    getLimitedAssets,
  };
}

// Re-export individual hooks for advanced usage
export { useAssetData } from "./useAssetData";
export { useAssetSearch } from "./useAssetSearch";
export { useAssetPagination } from "./useAssetPagination";
export { useAssetCategories } from "./useAssetCategories";
export { useAssetSelection } from "./useAssetSelection";

// Re-export types
export type { AssetDataState, AssetDataOptions } from "./useAssetData";
export type { SearchState, SearchOptions } from "./useAssetSearch";
export type { PaginationState, PaginationOptions } from "./useAssetPagination";
export type { CategoriesState, CategoriesOptions } from "./useAssetCategories";
export type { SelectionState, SelectionOptions } from "./useAssetSelection";
