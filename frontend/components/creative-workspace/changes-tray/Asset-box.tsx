import { useEffect, useRef } from "react";
import { AssetItem } from "./Asset-item";
import {
  OnRemoveAssetFunction,
  SceneConfiguration,
} from "@/lib/types/sceneConfig";
import { transformSceneConfiguration } from "@/lib/utils";

interface Asset {
  id: string;
  type: "image" | "setting";
  thumbnail: string;
  name?: string;
}

interface AssetBoxProps {
  isOpen: boolean;
  assets: SceneConfiguration;
  onRemoveAsset?: OnRemoveAssetFunction;
  hoveredAsset: string | null;
  onHoverAsset: (id: string | null) => void;
  onClose: () => void;
}

export function AssetBox({
  isOpen,
  assets,
  onRemoveAsset,
  hoveredAsset,
  onHoverAsset,
  onClose,
}: AssetBoxProps) {
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (boxRef.current && !boxRef.current.contains(event.target as Node)) {
        onClose();
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  const sceneConfig = transformSceneConfiguration(assets);
  return (
    <div ref={boxRef} className="relative">
      <div className="relative w-[200px] h-[200px] -translate-x-[88px] transition-all duration-300 ease-in-out">
        {sceneConfig.map((asset, index) => (
          <AssetItem
            key={asset.id}
            asset={asset}
            index={index}
            total={sceneConfig.length}
            onRemove={onRemoveAsset}
            isHovered={hoveredAsset === asset.id}
            onHover={onHoverAsset}
          />
        ))}
      </div>
    </div>
  );
}
