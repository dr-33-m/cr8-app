import { PolyHavenAsset } from "@/lib/services/polyhavenService";
import { AssetCard } from "./AssetCard";
import { EmptyState } from "@/components/placeholders/EmptyState";

interface AssetGridProps {
  assets: Array<PolyHavenAsset & { id: string }>;
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  compact?: boolean;
  loading?: boolean;
  error?: string;
}

export function AssetGrid({
  assets,
  onAssetSelect,
  compact = false,
  loading = false,
  error,
}: AssetGridProps) {
  // Loading skeleton
  if (loading) {
    const skeletonCount = compact ? 6 : 12;
    return (
      <div
        className={`grid gap-3 ${compact ? "grid-cols-2" : "grid-cols-3 lg:grid-cols-4"}`}
      >
        {Array.from({ length: skeletonCount }).map((_, i) => (
          <div
            key={i}
            className={`
              border rounded-lg overflow-hidden
              ${compact ? "h-32" : "h-48"}
            `}
          >
            <div
              className={`bg-secondary animate-pulse ${compact ? "h-20" : "h-32"}`}
            />
            <div className={`p-3 ${compact ? "py-2" : ""}`}>
              <div className="h-4 bg-secondary rounded animate-pulse mb-2" />
              {!compact && (
                <>
                  <div className="h-3 bg-secondary rounded animate-pulse mb-2 w-3/4" />
                  <div className="flex gap-1">
                    <div className="h-4 bg-secondary rounded animate-pulse w-12" />
                    <div className="h-4 bg-secondary rounded animate-pulse w-16" />
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Empty state - show only when API call was successful but returned no assets
  if (!error && assets.length === 0) {
    return (
      <EmptyState
        title="No assets found"
        description="Try adjusting your filters or search terms"
        icon={<div className="text-6xl">📦</div>}
        className="py-12"
      />
    );
  }

  // Asset grid
  return (
    <div
      className={`grid gap-3 ${compact ? "grid-cols-2" : "grid-cols-3 lg:grid-cols-4 xl:grid-cols-5"}`}
    >
      {assets.map((asset) => (
        <AssetCard
          key={asset.id}
          asset={asset}
          onSelect={onAssetSelect}
          compact={compact}
        />
      ))}
    </div>
  );
}
