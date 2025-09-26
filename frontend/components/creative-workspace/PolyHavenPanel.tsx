import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { RefreshCw } from "lucide-react";
import {
  AssetType,
  PolyHavenAsset,
  polyhavenService,
} from "@/lib/services/polyhavenService";
import { AssetGrid } from "./AssetGrid";
import { AssetFilters } from "./AssetFilters";
import { PolyHavenDialog } from "./PolyHavenDialog";

interface PolyHavenPanelProps {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
}

export function PolyHavenPanel({ onAssetSelect }: PolyHavenPanelProps) {
  const [selectedType, setSelectedType] = useState<AssetType>("textures");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [assets, setAssets] = useState<Record<string, PolyHavenAsset>>({});
  const [selectedAsset, setSelectedAsset] = useState<
    (PolyHavenAsset & { id: string }) | undefined
  >(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Load initial assets
  useEffect(() => {
    const loadAssets = async () => {
      setLoading(true);
      setError(undefined);
      try {
        const assetsData = await polyhavenService.getAssets(selectedType);
        setAssets(assetsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load assets");
        setAssets({});
      } finally {
        setLoading(false);
      }
    };

    loadAssets();
  }, [selectedType]);

  const handleAssetSelect = (asset: PolyHavenAsset & { id: string }) => {
    setSelectedAsset(asset);
    onAssetSelect?.(asset);
  };

  const handleRefresh = async () => {
    setLoading(true);
    setError(undefined);
    try {
      const assetsData = await polyhavenService.getAssets(selectedType);
      setAssets(assetsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load assets");
    } finally {
      setLoading(false);
    }
  };

  // Get limited assets for compact view (first 6)
  const limitedAssets = polyhavenService
    .convertAssetsToArray(assets)
    .slice(0, 6);

  const getAssetCount = () => {
    return Object.keys(assets).length;
  };

  return (
    <>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img
              src="/assets/polyhaven_256.png"
              alt="Poly Haven"
              className="w-6 h-6"
            />
            <h3 className="text-lg font-medium text-white">Poly Haven</h3>
            {!loading && (
              <Badge className="bg-orange-500/20 text-orange-300 border-orange-500/30 text-xs">
                {getAssetCount()}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-white/60 hover:text-white hover:bg-white/10"
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw
                className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
              />
            </Button>
          </div>
        </div>

        {/* Compact Filters */}
        <AssetFilters
          selectedType={selectedType}
          onTypeChange={setSelectedType}
          selectedCategories={selectedCategories}
          onCategoriesChange={setSelectedCategories}
          searchQuery=""
          onSearchChange={() => {}} // No search in compact mode
          compact
        />

        {/* Asset Grid */}
        <AssetGrid
          assets={limitedAssets}
          onAssetSelect={handleAssetSelect}
          selectedAsset={selectedAsset}
          loading={loading}
          error={error}
          compact
        />

        {/* Show more hint */}
        {!loading && !error && limitedAssets.length > 0 && (
          <div className="text-center">
            <Button
              variant="outline"
              size="sm"
              className="border-white/20 bg-white/5 text-white/60 hover:bg-white/10 hover:text-white"
              onClick={() => setDialogOpen(true)}
            >
              View All {getAssetCount()} Assets
            </Button>
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
          <div className="text-center py-4">
            <p className="text-red-400 text-sm mb-2">Failed to load assets</p>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              className="border-white/20 bg-white/5 text-white hover:bg-white/10"
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
        )}
      </div>

      {/* Expanded Dialog */}
      <PolyHavenDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onAssetSelect={onAssetSelect}
        initialType={selectedType}
      />
    </>
  );
}
