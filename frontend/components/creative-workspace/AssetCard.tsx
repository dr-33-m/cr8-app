import { useState } from "react";
import { PolyHavenAsset } from "@/lib/services/polyhavenService";
import { Download, ExternalLink, User } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";

interface AssetCardProps {
  asset: PolyHavenAsset & { id: string };
  onSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  isSelected?: boolean;
  compact?: boolean;
}

export function AssetCard({
  asset,
  onSelect,
  isSelected,
  compact = false,
}: AssetCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const formatDownloads = (count: number): string => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toString();
  };

  const getAssetTypeColor = (type: number) => {
    switch (type) {
      case 0:
        return "bg-blue-500/20 text-blue-300 border-blue-500/30"; // HDRIs
      case 1:
        return "bg-green-500/20 text-green-300 border-green-500/30"; // Textures
      case 2:
        return "bg-purple-500/20 text-purple-300 border-purple-500/30"; // Models
      default:
        return "bg-gray-500/20 text-gray-300 border-gray-500/30";
    }
  };

  const getAssetTypeName = (type: number) => {
    switch (type) {
      case 0:
        return "HDRI";
      case 1:
        return "Texture";
      case 2:
        return "Model";
      default:
        return "Asset";
    }
  };

  const handleCardClick = () => {
    onSelect?.(asset);
  };

  return (
    <Card
      className={`
        group relative overflow-hidden cursor-pointer transition-all duration-200
        ${
          isSelected
            ? "border-orange-500/50 bg-orange-500/10 shadow-lg shadow-orange-500/20"
            : "border-white/10 bg-white/5 hover:bg-white/10 hover:border-white/20"
        }
        ${compact ? "h-32" : "h-48"}
      `}
      onClick={handleCardClick}
    >
      {/* Image */}
      <div
        className={`relative overflow-hidden ${compact ? "h-full" : "h-32"}`}
      >
        {!imageLoaded && !imageError && (
          <div className="absolute inset-0 bg-gray-700 animate-pulse flex items-center justify-center">
            <div className="w-8 h-8 border-2 border-white/20 border-t-white/60 rounded-full animate-spin" />
          </div>
        )}

        {imageError ? (
          <div className="absolute inset-0 bg-gray-700 flex items-center justify-center">
            <div className="text-white/40 text-sm">No preview</div>
          </div>
        ) : (
          <img
            src={asset.thumbnail_url}
            alt={asset.name}
            className={`
              w-full h-full object-cover transition-all duration-200
              group-hover:scale-110
              ${imageLoaded ? "opacity-100" : "opacity-0"}
            `}
            onLoad={() => setImageLoaded(true)}
            onError={() => setImageError(true)}
          />
        )}

        {/* Type badge - only show in non-compact mode */}
        {!compact && (
          <Badge
            className={`
              absolute top-2 left-2 text-xs px-2 py-1 border
              ${getAssetTypeColor(asset.type)}
            `}
          >
            {getAssetTypeName(asset.type)}
          </Badge>
        )}

        {/* Download count - only show in non-compact mode */}
        {!compact && (
          <div className="absolute top-2 right-2 flex items-center gap-1 bg-black/60 backdrop-blur-sm rounded px-2 py-1">
            <Download className="w-3 h-3 text-white/70" />
            <span className="text-xs text-white/70">
              {formatDownloads(asset.download_count)}
            </span>
          </div>
        )}
      </div>

      {/* Content - only show in non-compact mode */}
      {!compact && (
        <div className="p-3">
          <h3 className="font-medium text-white line-clamp-1">{asset.name}</h3>

          {/* Authors */}
          <div className="flex items-center gap-1 mt-1 text-xs text-white/60">
            <User className="w-3 h-3" />
            <span className="line-clamp-1">
              {Object.keys(asset.authors).join(", ")}
            </span>
          </div>

          {/* Categories */}
          <div className="flex flex-wrap gap-1 mt-2">
            {asset.categories.slice(0, 2).map((category) => (
              <Badge
                key={category}
                variant="outline"
                className="text-xs px-1 py-0 border-white/20 text-white/60"
              >
                {category}
              </Badge>
            ))}
            {asset.categories.length > 2 && (
              <Badge
                variant="outline"
                className="text-xs px-1 py-0 border-white/20 text-white/60"
              >
                +{asset.categories.length - 2}
              </Badge>
            )}
          </div>
        </div>
      )}

      {/* Hover overlay with actions */}
      <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center gap-2">
        <Button
          size="sm"
          variant="outline"
          className="border-white/20 bg-white/10 text-white hover:bg-white/20"
          onClick={(e) => {
            e.stopPropagation();
            window.open(`https://polyhaven.com/a/${asset.id}`, "_blank");
          }}
        >
          <ExternalLink className="w-4 h-4 mr-1" />
          View
        </Button>

        <Button
          size="sm"
          className="bg-orange-500 hover:bg-orange-600 text-white"
          onClick={(e) => {
            e.stopPropagation();
            onSelect?.(asset);
          }}
        >
          Select
        </Button>
      </div>
    </Card>
  );
}
