/** Which face of the right-hand card is showing. */
export type RightPanel = "assets" | "chat";

export interface VisibilityState {
  isSceneControlsVisible: boolean;
  isAssetSelectionVisible: boolean;
  isBottomControlsVisible: boolean;
  isFullscreen: boolean;
  /** The right-hand card carousels between the asset browser and B.L.A.Z.E's chat. */
  rightPanel: RightPanel;
  setSceneControlsVisible: (visible: boolean) => void;
  setAssetSelectionVisible: (visible: boolean) => void;
  setBottomControlsVisible: (visible: boolean) => void;
  setIsFullscreen: (isFullscreen: boolean) => void;
  setRightPanel: (panel: RightPanel) => void;
  /** Slide to a panel and make sure the card is actually open. */
  showRightPanel: (panel: RightPanel) => void;
  toggleSceneControls: () => void;
  toggleAssetSelection: () => void;
  toggleBottomControls: () => void;
  toggleFullscreen: () => void;
  reset: () => void;
}
