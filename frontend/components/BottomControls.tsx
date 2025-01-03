import { Button } from "@/components/ui/button";
import {
  Play,
  ChevronDown,
  ChevronUp,
  Clapperboard,
  LoaderPinwheel,
  Pause,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { DesignTray } from "./creative-workspace/changes-tray";
import {
  OnRemoveAssetFunction,
  SceneConfiguration,
} from "@/lib/types/sceneConfig";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";

interface BottomControlsProps {
  isLoading: boolean;
  isPlaying: boolean;
  isFinalVideoReady: boolean;
  onShootPreview: () => void;
  onPlaybackPreview: () => void;
  onStopPlaybackPreview: () => void;
  onGenerateVideo: () => void;
  assets: SceneConfiguration;
  onRemoveAsset?: OnRemoveAssetFunction;
}

export function BottomControls({ children }) {
  const isVisible = useVisibilityStore(
    (state) => state.isBottomControlsVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleBottomControls
  );

  return (
    <div
      className={`absolute bottom-4 left-1/2 transform -translate-x-1/2 transition-all duration-300 
      ${isVisible ? "translate-y-0" : "translate-y-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute left-1/2 -top-12 -translate-x-1/2 text-white hover:bg-white/10"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronDown className="h-6 w-6" />
        ) : (
          <ChevronUp className="h-6 w-6" />
        )}
      </Button>
      <div className="backdrop-blur-md bg-white/5 rounded-lg px-6 py-3 flex items-center space-x-6">
        {children}
      </div>
    </div>
  );
}
