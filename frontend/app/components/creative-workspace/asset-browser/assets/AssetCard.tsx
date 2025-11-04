import { useState } from "react";
import { PolyHavenAsset } from "@/lib/services/polyhavenService";
import { Download, User, Info } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  HoverCard,
  HoverCardContent,
  HoverCardTrigger,
} from "@/components/ui/hover-card";
import useInboxStore from "@/store/inboxStore";
import { toast } from "sonner";
import { formatDownloads, getAssetTypeName } from "@/lib/utils";

interface AssetCardProps {
  asset: PolyHavenAsset & { id: string };
  onSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  isSelected?: boolean;
  compact?: boolean;
}

export function AssetCard({
  asset,
  onSelect,
  compact = false,
}: AssetCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

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
          group relative overflow-hidden cursor-pointer
          ${isInInbox ? "border-primary/50 bg-primary/10 shadow-lg shadow-primary/20" : ""}
          ${compact ? "h-32" : "h-48"}
        `}
        onClick={handleCardClick}
      >
        <div className="relative overflow-hidden h-full">
          {!imageLoaded && !imageError && (
            <div className="absolute inset-0 bg-secondary animate-pulse flex items-center justify-center">
              <div className="w-8 h-8 border-2 border-t-secondary rounded-full animate-spin" />
            </div>
          )}

          {imageError ? (
            <div className="absolute inset-0 bg-secondary flex items-center justify-center">
              <div className="text-muted-foreground text-sm">No preview</div>
            </div>
          ) : (
            <img
              src={asset.thumbnail_url}
              alt={asset.name}
              className={`
                w-full h-full object-contain
                group-hover:scale-105
                ${imageLoaded ? "opacity-100" : "opacity-0"}
              `}
              onLoad={() => setImageLoaded(true)}
              onError={() => setImageError(true)}
            />
          )}

          {!compact && (
            <HoverCardTrigger asChild>
              <Info
                className="w-4 h-4 top-2 right-2 absolute text-muted-foreground hover:text-primary"
                onClick={(e) => e.stopPropagation()}
              />
            </HoverCardTrigger>
          )}
        </div>
      </Card>

      <HoverCardContent className="w-80" side="top">
        <div className="space-y-3">
          <div>
            <h4 className="font-medium text-lg">{asset.name}</h4>
            <div className="flex items-center gap-2 mt-1">
              <Badge className="text-xs" variant="secondary">
                {getAssetTypeName(asset.type)}
              </Badge>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Download className="w-3 h-3" />
                <span>{formatDownloads(asset.download_count)}</span>
              </div>
            </div>
          </div>

          <div>
            <div className="text-sm text-muted-foreground mb-1">Authors:</div>
            <div className="flex items-center gap-1 text-sm">
              <User className="w-3 h-3 text-muted-foreground" />
              <span>{Object.keys(asset.authors).join(", ")}</span>
            </div>
          </div>

          <div>
            <div className="text-sm text-muted-foreground mb-1">
              Resolution:
            </div>
            <div className="text-sm">{asset.max_resolution.join(" × ")}</div>
          </div>

          <div>
            <div className="text-sm text-muted-foreground mb-2">
              Categories:
            </div>
            <div className="flex flex-wrap gap-1">
              {asset.categories.map((category) => (
                <Badge key={category} variant="outline" className="text-xs">
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
