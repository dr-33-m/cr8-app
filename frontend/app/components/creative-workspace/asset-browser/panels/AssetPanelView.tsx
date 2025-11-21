import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CardContent } from "@/components/ui/card";
import { RefreshCw } from "lucide-react";
import { AssetGrid } from "../grids";
import { ErrorComponent } from "@/components/errors/ErrorComponent";
import { AssetTypeTabs, AssetSearchInput } from "../filters";
import polyhaveLogo from "@/assets/polyhaven_256.png";
import { AssetPanelViewProps } from "@/lib/types/assetBrowser";

const ASSETS_PREVIEW_LIMIT = 6;

export function AssetPanelView({
  assetBrowser,
  onShowDialog,
}: AssetPanelViewProps) {
  const {
    selectedType,
    searchQuery,
    loading,
    error,
    totalCount,
    setType,
    setSearch,
    clearSearch,
    selectAsset,
    refresh,
    getLimitedAssets,
  } = assetBrowser;

  const limitedAssets = getLimitedAssets(ASSETS_PREVIEW_LIMIT);
  const hasAssets = !loading && !error && limitedAssets.length > 0;

  const handleRefresh = () => {
    refresh();
  };

  return (
    <CardContent className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <img src={polyhaveLogo} alt="Poly Haven" className="w-6 h-6" />
          <h3 className="text-lg font-medium">Poly Haven</h3>
          {!loading && (
            <Badge className="bg-primary/20 text-primary-foreground border-primary/30 text-xs">
              {totalCount}
            </Badge>
          )}
        </div>

        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={handleRefresh}
          disabled={loading}
          aria-label="Refresh assets"
        >
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {/* Filters */}
      <AssetTypeTabs selectedType={selectedType} onTypeChange={setType} />

      <AssetSearchInput
        value={searchQuery}
        onChange={setSearch}
        onClear={clearSearch}
        placeholder="Search assets..."
        compact
      />

      {/* Asset Grid */}
      <AssetGrid
        assets={limitedAssets}
        onAssetSelect={selectAsset}
        loading={loading}
        error={error}
        compact
      />

      {/* View All Button */}
      {hasAssets && (
        <div className="text-center">
          <Button variant="outline" size="sm" onClick={onShowDialog}>
            View All {totalCount} Assets
          </Button>
        </div>
      )}

      {/* Error State */}
      {error && !loading && (
        <ErrorComponent
          message="Failed to load assets"
          action={handleRefresh}
          actionText="Retry"
          actionIcon={<RefreshCw className="w-4 h-4 mr-2" />}
        />
      )}
    </CardContent>
  );
}
