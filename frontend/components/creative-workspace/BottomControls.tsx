import { Button } from "@/components/ui/button";
import {
  Play,
  ChevronDown,
  ChevronUp,
  Clapperboard,
  CirclePlus,
} from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { DesignTray } from "./design-tray";
import { Asset } from "@/app/routes/project";

interface BottomControlsProps {
  isVisible: boolean;
  onToggleVisibility: () => void;
  onShootPreview: () => void;
  onPlaybackPreview: () => void;
  assets?: Asset[];
  onRemoveAsset?: (id: string) => void;
  onAddAsset?: () => void;
}

export function BottomControls({
  isVisible,
  onToggleVisibility,
  onShootPreview,
  onPlaybackPreview,
  assets = [],
  onRemoveAsset,
  onAddAsset,
}: BottomControlsProps) {
  const [isAssetBoxOpen, setIsAssetBoxOpen] = useState(false);
  const assetBoxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        assetBoxRef.current &&
        !assetBoxRef.current.contains(event.target as Node)
      ) {
        setIsAssetBoxOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

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
        <Button
          variant="ghost"
          size="icon"
          className="text-[#0077B6] hover:bg-[#0077B6]/10"
          title="Shoot Preview"
          onClick={onShootPreview}
        >
          <Clapperboard className="h-6 w-6" />
          <span className="sr-only">Shoot Preview</span>
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-[#FFD100] hover:bg-[#FFD100]/10"
          title="Play Preview"
          onClick={onPlaybackPreview}
        >
          <Play className="h-6 w-6" />
          <span className="sr-only">Play Preview</span>
        </Button>
        <div className="h-8 w-px bg-white/20" />
        <DesignTray
          onClick={() => setIsAssetBoxOpen(!isAssetBoxOpen)}
          isActive={isAssetBoxOpen}
          assets={assets}
          onRemoveAsset={onRemoveAsset}
          onClose={() => setIsAssetBoxOpen(false)}
        />
        <Button
          variant="ghost"
          size="icon"
          className="text-white hover:bg-white/10"
          title="Add Asset"
          onClick={onAddAsset}
        >
          <CirclePlus className="h-6 w-6" />
          <span className="sr-only">Add Asset</span>
        </Button>
      </div>
    </div>
  );
}
