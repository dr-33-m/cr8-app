import { RefObject, ReactNode } from "react";

// Creative Workspace interfaces
export interface ControlsOverlayProps {
  children: ReactNode;
}

export interface SceneViewPortProps {
  videoRef: RefObject<HTMLVideoElement>;
  isConnected: boolean;
}
