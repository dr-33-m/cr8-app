import { VisibilityState } from "@/lib/types/controlsVisibility";
import { create } from "zustand";

export const useVisibilityStore = create<VisibilityState>((set) => ({
  isSceneControlsVisible: true,
  isAssetSelectionVisible: true,
  isBottomControlsVisible: true,
  isFullscreen: false,
  rightPanel: "assets",
  setRightPanel: (panel) => set({ rightPanel: panel }),
  // Clicking B.L.A.Z.E in the bottom controls should get you to the chat even if
  // the card is collapsed, so opening and sliding are one action.
  showRightPanel: (panel) =>
    set({ rightPanel: panel, isAssetSelectionVisible: true }),
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
      rightPanel: "assets",
    }),
}));
