export interface VisibilityState {
  isSceneControlsVisible: boolean;
  isAssetSelectionVisible: boolean;
  isBottomControlsVisible: boolean;
  isFullscreen: boolean;
  setSceneControlsVisible: (visible: boolean) => void;
  setAssetSelectionVisible: (visible: boolean) => void;
  setBottomControlsVisible: (visible: boolean) => void;
  setIsFullscreen: (isFullscreen: boolean) => void;
  toggleSceneControls: () => void;
  toggleAssetSelection: () => void;
  toggleBottomControls: () => void;
  toggleFullscreen: () => void;
  reset: () => void;
}
