import { VisibilityState } from "@/lib/types/controlsVisibility";
import { create } from "zustand";

export const useVisibilityStore = create<VisibilityState>((set) => ({
  isSceneControlsVisible: true,
  isAssetSelectionVisible: true,
  isBottomControlsVisible: true,
  isFullscreen: false,
  setSceneControlsVisible: (visible) =>
    set({ isSceneControlsVisible: visible }),
  setAssetSelectionVisible: (visible) =>
    set({ isAssetSelectionVisible: visible }),
  setBottomControlsVisible: (visible) =>
    set({ isBottomControlsVisible: visible }),
  setIsFullscreen: (isFullscreen) =>
    set((state) => ({
      isFullscreen,
      isSceneControlsVisible: !isFullscreen,
      isAssetSelectionVisible: !isFullscreen,
      isBottomControlsVisible: !isFullscreen,
    })),
  toggleSceneControls: () =>
    set((state) => ({ isSceneControlsVisible: !state.isSceneControlsVisible })),
  toggleAssetSelection: () =>
    set((state) => ({
      isAssetSelectionVisible: !state.isAssetSelectionVisible,
    })),
  toggleBottomControls: () =>
    set((state) => ({
      isBottomControlsVisible: !state.isBottomControlsVisible,
    })),
  toggleFullscreen: () =>
    set((state) => ({
      isFullscreen: !state.isFullscreen,
      isSceneControlsVisible: state.isFullscreen,
      isAssetSelectionVisible: state.isFullscreen,
      isBottomControlsVisible: state.isFullscreen,
    })),
  reset: () =>
    set({
      isSceneControlsVisible: true,
      isAssetSelectionVisible: true,
      isBottomControlsVisible: true,
      isFullscreen: false,
    }),
}));
