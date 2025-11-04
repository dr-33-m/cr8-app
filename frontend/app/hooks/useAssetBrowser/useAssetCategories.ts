import { useState, useCallback, useEffect } from "react";
import { polyhavenService } from "@/lib/services/polyhavenService";
import {
  AssetType,
  CategoriesResponse,
  CategoriesState,
  CategoriesOptions,
} from "@/lib/types/assetBrowser";

export function useAssetCategories(options: CategoriesOptions = {}) {
  const { assetType, initialCategories = [], enabled = true } = options;

  const [state, setState] = useState<CategoriesState>({
    categories: {},
    selectedCategories: initialCategories,
    loading: false,
    error: undefined,
  });

  const loadCategories = useCallback(async () => {
    if (!enabled || !assetType) return;

    setState((prev) => ({ ...prev, loading: true, error: undefined }));

    try {
      const categoriesData = await polyhavenService.getCategories(assetType);
      setState((prev) => ({
        ...prev,
        categories: categoriesData,
        loading: false,
        error: undefined,
      }));
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to load categories";
      setState((prev) => ({
        ...prev,
        loading: false,
        error: errorMessage,
      }));
    }
  }, [assetType, enabled]);

  const toggleCategory = useCallback((category: string) => {
    setState((prev) => ({
      ...prev,
      selectedCategories: prev.selectedCategories.includes(category)
        ? prev.selectedCategories.filter((c) => c !== category)
        : [...prev.selectedCategories, category],
    }));
  }, []);

  const addCategory = useCallback((category: string) => {
    setState((prev) => ({
      ...prev,
      selectedCategories: prev.selectedCategories.includes(category)
        ? prev.selectedCategories
        : [...prev.selectedCategories, category],
    }));
  }, []);

  const removeCategory = useCallback((category: string) => {
    setState((prev) => ({
      ...prev,
      selectedCategories: prev.selectedCategories.filter((c) => c !== category),
    }));
  }, []);

  const setCategories = useCallback((categories: string[]) => {
    setState((prev) => ({ ...prev, selectedCategories: categories }));
  }, []);

  const clearCategories = useCallback(() => {
    setState((prev) => ({ ...prev, selectedCategories: [] }));
  }, []);

  const clearError = useCallback(() => {
    setState((prev) => ({ ...prev, error: undefined }));
  }, []);

  // Auto-load categories when asset type changes
  useEffect(() => {
    loadCategories();
  }, [loadCategories]);

  // Reset selected categories when asset type changes
  useEffect(() => {
    setState((prev) => ({ ...prev, selectedCategories: [] }));
  }, [assetType]);

  return {
    ...state,
    toggleCategory,
    addCategory,
    removeCategory,
    setCategories,
    clearCategories,
    clearError,
    refresh: loadCategories,
  };
}
