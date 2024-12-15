import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { OnRemoveAssetFunction } from "@/lib/types/sceneConfig";
import { Sun, Camera, X } from "lucide-react";
import { useState } from "react";

interface AssetItemProps {
  asset: {
    id: string;
    type: "light" | "camera";
    name?: string;
  };
  index: number;
  total: number;
  onRemove?: OnRemoveAssetFunction;
  isHovered: boolean;
  onHover: (id: string | null) => void;
}

export function AssetItem({
  asset,
  index,
  total,
  onRemove,
  isHovered,
  onHover,
}: AssetItemProps) {
  const [isOpen, setIsOpen] = useState(false);
  const angle = (index * 2 * Math.PI) / total - Math.PI / 2;
  const radius = 80;
  const x = Math.cos(angle) * radius;
  const y = Math.sin(angle) * radius;

  const renderAssetProperty = (key: string, value: any) => {
    if (key === "id" || key === "type") return null;

    return (
      <div
        key={key}
        className="flex justify-between items-center py-2 border-b border-white/10 last:border-b-0"
      >
        <span className="text-white/60 capitalize">{key}:</span>
        {key === "color" ? (
          <span className="font-medium flex items-center gap-2">
            <div
              className="w-4 h-4 rounded-full"
              style={{ backgroundColor: value }}
            ></div>
            {value}
          </span>
        ) : key === "strength" ? (
          <span className="font-medium">{`${value}W`}</span>
        ) : (
          <span className="font-medium">{value}</span>
        )}
      </div>
    );
  };

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <div
          className={`absolute transition-all duration-300 ease-in-out opacity-100 scale-100`}
          style={{
            left: `calc(50% + ${x}px)`,
            top: `calc(50% + ${y}px)`,
            transform: "translate(-50%, -50%)",
          }}
          onMouseEnter={() => onHover(asset.id)}
          onMouseLeave={() => onHover(null)}
        >
          <div
            className={`w-12 h-12 rounded-full bg-white/10 flex items-center justify-center
        cursor-pointer transition-all duration-200 border border-white/20
        hover:border-white/60 group relative
        ${isHovered ? "border-white/60" : ""}`}
            title={`${asset.type} changes` || `Asset ${asset.id}`}
          >
            {asset.type === "light" ? (
              <Sun className="h-5 w-5 text-white" />
            ) : (
              <Camera className="h-5 w-5 text-white" />
            )}
            {isHovered && onRemove && (
              <button
                className="absolute -top-1 -right-1 p-1 rounded-full bg-white/10 
            border border-white/20 hover:border-white/60 text-white/80 hover:text-white
            transition-all duration-200"
                onClick={(e) => {
                  e.stopPropagation();
                  onRemove(asset.type, asset.name);
                }}
              >
                <X className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>
      </PopoverTrigger>
      <PopoverContent className="w-80 bg-white/10 backdrop-blur-md border border-white/20 rounded-xl p-4 text-white">
        <div className="space-y-4">
          <h3 className="font-semibold text-lg border-b border-white/20 pb-2">
            {asset.type.charAt(0).toUpperCase() + asset.type.slice(1)} Changes
          </h3>
          <div className="space-y-2">
            {Object.entries(asset).map(([key, value]) =>
              renderAssetProperty(key, value)
            )}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
