import { create } from "zustand";
import { persist } from "zustand/middleware";
import {
  Asset,
  AssetPlacerState,
  PlacedAsset,
  STATIC_ASSETS,
} from "@/lib/types/assetPlacer";

export const useAssetPlacerStore = create<AssetPlacerState>()(
  persist(
    (set, get) => ({
      availableAssets: STATIC_ASSETS, // Initial static data
      placedAssets: [],
      selectedAssetId: null,

      setAvailableAssets: (assets) => set({ availableAssets: assets }),

      selectAsset: (id) => set({ selectedAssetId: id }),

      placeAsset: (assetId, emptyName) =>
        set((state) => ({
          placedAssets: [
            ...state.placedAssets.filter((a) => a.assetId !== assetId),
            { assetId, emptyName },
          ],
        })),

      removePlacedAsset: (assetId) =>
        set((state) => ({
          placedAssets: state.placedAssets.filter((a) => a.assetId !== assetId),
        })),

      updatePlacedAsset: (assetId, updates) =>
        set((state) => ({
          placedAssets: state.placedAssets.map((asset) =>
            asset.assetId === assetId ? { ...asset, ...updates } : asset
          ),
        })),

      isAssetPlaced: (assetId) => {
        return get().placedAssets.some((asset) => asset.assetId === assetId);
      },

      getPlacedAssetByEmptyName: (emptyName) => {
        return get().placedAssets.find(
          (asset) => asset.emptyName === emptyName
        );
      },

      getEmptyNameForAsset: (assetId) => {
        return get().placedAssets.find((asset) => asset.assetId === assetId)
          ?.emptyName;
      },

      clearPlacedAssets: () => set({ placedAssets: [] }),
    }),
    {
      name: "asset-placer-storage",
      partialize: (state) => ({
        placedAssets: state.placedAssets,
      }),
    }
  )
);
