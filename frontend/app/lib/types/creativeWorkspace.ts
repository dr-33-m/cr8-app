import { RefObject, ReactNode } from "react";
import type { InstanceStatus } from "@/contexts/WebSocketContext";

// Creative Workspace interfaces
export interface ControlsOverlayProps {
  children: ReactNode;
}

export interface SceneViewPortProps {
  videoRef: RefObject<HTMLVideoElement>;
  isConnected: boolean;
  instanceStatus?: InstanceStatus | null;
  cancelLaunch?: () => void;
  onRetry?: () => void;
}
