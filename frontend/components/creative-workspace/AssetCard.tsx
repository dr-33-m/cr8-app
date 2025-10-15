import { useState } from "react";
import {
  PolyHavenAsset,
  polyhavenService,
} from "@/lib/services/polyhavenService";
import { Download, ExternalLink, User, Info } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import useInboxStore from "@/store/inboxStore";
import { toast } from "sonner";

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

  const inboxStore = useInboxStore();
  const isInInbox = inboxStore.hasItem(asset.id);

  const handleCardClick = () => {
    const wasInInbox = inboxStore.hasItem(asset.id);
    inboxStore.toggleItem(asset);

    if (wasInInbox) {
      toast.info(`Removed ${asset.name} from inbox`);
    } else {
      toast.success(`Added ${asset.name} to inbox`);
    }

    // Call the optional onSelect prop if provided
    onSelect?.(asset);
  };

  return (
    <HoverCard>
      <Card
        className={`
          group relative overflow-hidden cursor-pointer transition-all duration-200
          ${
            isInInbox
              ? "border-primary/50 bg-primary/10 shadow-lg shadow-primary/20"
              : "border-white/10 bg-cr8-charcoal/10 backdrop-blur-md hover:border-white/20"
          }
          ${compact ? "h-32" : "h-48"}
        `}
        onClick={handleCardClick}
      >
        {/* Full Image */}
        <div className="relative overflow-hidden h-full">
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
                w-full h-full object-contain transition-all duration-200
                group-hover:scale-105
                ${imageLoaded ? "opacity-100" : "opacity-0"}
              `}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />
          )}

          {/* Info Icon Trigger */}
          {!compact && (
            <HoverCardTrigger asChild>
              <Info
                className="w-4 h-4 top-2 right-2 absolute text-white/60 hover:text-primary"
                onClick={(e) => e.stopPropagation()}
              />
            </HoverCardTrigger>
          )}
        </div>
      </Card>

      {/* HoverCard Content outside the card */}
      <HoverCardContent
        className="w-80 bg-cr8-charcoal/40 backdrop-blur-md border-white/10 text-white"
        side="top"
      >
        <div className="space-y-3">
          <div>
            <h4 className="font-medium text-lg">{asset.name}</h4>
            <div className="flex items-center gap-2 mt-1">
              <Badge className={`text-xs ${getAssetTypeColor(asset.type)}`}>
                {getAssetTypeName(asset.type)}
              </Badge>
              <div className="flex items-center gap-1 text-xs text-white/60">
                <Download className="w-3 h-3" />
                <span>{formatDownloads(asset.download_count)} downloads</span>
              </div>
            </div>
          </div>

          <div>
            <div className="text-sm text-white/60 mb-1">Authors:</div>
            <div className="flex items-center gap-1 text-sm">
              <User className="w-3 h-3 text-white/60" />
              <span>{Object.keys(asset.authors).join(", ")}</span>
            </div>
          </div>

          <div>
            <div className="text-sm text-white/60 mb-1">Resolution:</div>
            <div className="text-sm">{asset.max_resolution.join(" × ")}</div>
          </div>

          <div>
            <div className="text-sm text-white/60 mb-2">Categories:</div>
            <div className="flex flex-wrap gap-1">
              {asset.categories.map((category) => (
                <Badge
                  key={category}
                  variant="outline"
                  className="text-xs border-white/20 text-white/60"
                >
                  {category}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </HoverCardContent>
    </HoverCard>
  );
}
