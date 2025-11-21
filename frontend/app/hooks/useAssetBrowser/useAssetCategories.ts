import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { createCategoriesQueryOptions } from "@/server/query-manager/polyhaven";
import type { AssetType, CategoriesOptions } from "@/lib/types/assetBrowser";

export function useAssetCategories(options: CategoriesOptions = {}) {
  const { assetType, initialCategories = [], enabled = true } = options;

  // UI state for selected categories (managed locally)
  const [selectedCategories, setSelectedCategories] =
    useState<string[]>(initialCategories);

  // Server state for available categories (managed by React Query)
  // Only destructure what you need to avoid unnecessary re-renders
  const {
    data: categories = {},
    isLoading,
    error,
    refetch,
  } = useQuery(
    createCategoriesQueryOptions(assetType as AssetType, undefined, {
      enabled: enabled && !!assetType,
    })
  );

  // These don't need useCallback since they don't depend on any props/state
  // and setSelectedCategories is stable
  const toggleCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category)
        ? prev.filter((c) => c !== category)
        : [...prev, category]
    );
  };

  const addCategory = (category: string) => {
    setSelectedCategories((prev) =>
      prev.includes(category) ? prev : [...prev, category]
    );
  };

  const removeCategory = (category: string) => {
    setSelectedCategories((prev) => prev.filter((c) => c !== category));
  };

  const clearCategories = () => {
    setSelectedCategories([]);
  };

  // Return a stable object structure
  return {
    // State
    categories,
    selectedCategories,
    loading: isLoading,
    error: error instanceof Error ? error.message : null,

    // Actions
    toggleCategory,
    addCategory,
    removeCategory,
    setCategories: setSelectedCategories,
    clearCategories,
    refresh: refetch,
  };
}
