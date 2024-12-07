import { ImageIcon, Settings, X } from "lucide-react";

interface AssetItemProps {
  asset: {
    id: string;
    type: "image" | "setting";
    name?: string;
  };
  index: number;
  total: number;
  onRemove?: (id: string) => void;
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
  const angle = (index * 2 * Math.PI) / total - Math.PI / 2;
  const radius = 80;
  const x = Math.cos(angle) * radius;
  const y = Math.sin(angle) * radius;

  return (
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
        title={asset.name || `Asset ${asset.id}`}
      >
        {asset.type === "image" ? (
          <ImageIcon className="h-5 w-5 text-white" />
        ) : (
          <Settings className="h-5 w-5 text-white" />
        )}
        {isHovered && onRemove && (
          <button
            className="absolute -top-1 -right-1 p-1 rounded-full bg-white/10 
            border border-white/20 hover:border-white/60 text-white/80 hover:text-white
            transition-all duration-200"
            onClick={(e) => {
              e.stopPropagation();
              onRemove(asset.id);
            }}
          >
            <X className="h-3 w-3" />
          </button>
        )}
      </div>
    </div>
  );
}
