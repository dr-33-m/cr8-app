import { useState } from "react";
import { useAssetData } from "./useAssetData";
import { useAssetSearch } from "./useAssetSearch";
import { useAssetPagination } from "./useAssetPagination";
import { useAssetCategories } from "./useAssetCategories";
import { useAssetSelection } from "./useAssetSelection";
import { AssetType, UseAssetBrowserOptions } from "@/lib/types/assetBrowser";

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

  // Calculate derived pagination state from server data
  const totalPages = Math.ceil(assetData.totalCount / pagination.limit);
  const hasNext = pagination.page < totalPages;
  const hasPrev = pagination.page > 1;

  // Handle asset type change
  const handleTypeChange = (type: AssetType) => {
    setSelectedType(type);
    search.clearQuery();
    categories.clearCategories();
    pagination.reset();
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

    // Pagination (derived + local state)
    pagination: {
      page: pagination.page,
      limit: pagination.limit,
      totalPages,
      hasNext,
      hasPrev,
    },

    // Selection
    selectedAsset: selection.selectedAsset,

    // Actions
    setType: handleTypeChange,
    setSearch: search.setQuery,
    clearSearch: search.clearQuery,

    // Category actions
    toggleCategory: categories.toggleCategory,
    addCategory: categories.addCategory,
    removeCategory: categories.removeCategory,
    setCategories: categories.setCategories,
    clearCategories: categories.clearCategories,

    // Pagination actions
    setPage: pagination.setPage,
    nextPage: hasNext ? pagination.nextPage : () => {},
    prevPage: hasPrev ? pagination.prevPage : () => {},
    firstPage: pagination.firstPage,
    lastPage: () => pagination.lastPage(totalPages),

    // Selection actions
    selectAsset: selection.selectAsset,
    clearSelection: selection.clearSelection,

    // Utility actions
    refresh: assetData.refresh,

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
