import { PolyHavenAsset } from "@/lib/services/polyhavenService";
import { AssetCard } from "./AssetCard";

interface AssetGridProps {
  assets: Array<PolyHavenAsset & { id: string }>;
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  selectedAsset?: PolyHavenAsset & { id: string };
  compact?: boolean;
  loading?: boolean;
  error?: string;
}

export function AssetGrid({
  assets,
  onAssetSelect,
  selectedAsset,
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
              bg-white/5 border border-white/10 rounded-lg overflow-hidden
              ${compact ? "h-32" : "h-48"}
            `}
          >
            <div
              className={`bg-gray-700 animate-pulse ${compact ? "h-20" : "h-32"}`}
            />
            <div className={`p-3 ${compact ? "py-2" : ""}`}>
              <div className="h-4 bg-gray-700 rounded animate-pulse mb-2" />
              {!compact && (
                <>
                  <div className="h-3 bg-gray-700 rounded animate-pulse mb-2 w-3/4" />
                  <div className="flex gap-1">
                    <div className="h-4 bg-gray-700 rounded animate-pulse w-12" />
                    <div className="h-4 bg-gray-700 rounded animate-pulse w-16" />
                  </div>
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="text-red-400 text-6xl mb-4">⚠️</div>
        <h3 className="text-lg font-medium text-white mb-2">
          Unable to load assets
        </h3>
        <p className="text-white/60 text-sm max-w-md">{error}</p>
      </div>
    );
  }

  // Empty state
  if (!assets || assets.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-12 text-center">
        <div className="text-white/40 text-6xl mb-4">📦</div>
        <h3 className="text-lg font-medium text-white mb-2">No assets found</h3>
        <p className="text-white/60 text-sm">
          Try adjusting your filters or search terms
        </p>
      </div>
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
          isSelected={selectedAsset?.id === asset.id}
          compact={compact}
        />
      ))}
    </div>
  );
}
