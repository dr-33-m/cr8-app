import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { CardContent } from "@/components/ui/card";
import { RefreshCw } from "lucide-react";
import { AssetGrid } from "../grids";
import { ErrorComponent } from "@/components/errors/ErrorComponent";
import {
  AssetTypeTabs,
  AssetSearchInput,
  CategoryFilterPopover,
  SelectedCategoriesDisplay,
} from "../filters";
import polyhaveLogo from "@/assets/polyhaven_256.png";
import { AssetPanelViewProps } from "@/lib/types/assetBrowser";

export function AssetPanelView({
  assetBrowser,
  onShowDialog,
  onAssetSelect,
}: AssetPanelViewProps) {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  const handleRefresh = () => {
    assetBrowser.refresh();
  };

  const handleTypeChange = (type: typeof assetBrowser.selectedType) => {
    assetBrowser.setType(type);
  };

  const handleSearchChange = (value: string) => {
    assetBrowser.setSearch(value);
  };

  const handleSearchClear = () => {
    assetBrowser.clearSearch();
  };

  const handleCategoriesChange = (categories: string[]) => {
    setSelectedCategories(categories);
    assetBrowser.setCategories(categories);
  };

  // Get limited assets for compact view
  const limitedAssets = assetBrowser.getLimitedAssets(6);

  return (
    <CardContent className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <img src={polyhaveLogo} alt="Poly Haven" className="w-6 h-6" />
          <h3 className="text-lg font-medium">Poly Haven</h3>
          {!assetBrowser.loading && (
            <Badge className="bg-primary/20 text-primary-foreground white border-primary/30 text-xs">
              {assetBrowser.totalCount}
            </Badge>
          )}
        </div>

        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="icon"
            className="h-8 w-8"
            onClick={handleRefresh}
            disabled={assetBrowser.loading}
          >
            <RefreshCw
              className={`h-4 w-4 ${assetBrowser.loading ? "animate-spin" : ""}`}
            />
          </Button>
        </div>
      </div>

      {/* Filter Tabs */}
      <AssetTypeTabs
        selectedType={assetBrowser.selectedType}
        onTypeChange={handleTypeChange}
      />

      {/* Search Input */}
      <AssetSearchInput
        value={assetBrowser.searchQuery}
        onChange={handleSearchChange}
        onClear={handleSearchClear}
        placeholder="Search assets..."
        compact
      />

      {/* Asset Grid */}
      <AssetGrid
        assets={limitedAssets}
        onAssetSelect={assetBrowser.selectAsset}
        loading={assetBrowser.loading}
        error={assetBrowser.error}
        compact
      />

      {/* Show more hint */}
      {!assetBrowser.loading &&
        !assetBrowser.error &&
        limitedAssets.length > 0 && (
          <div className="text-center">
            <Button variant="outline" size="sm" onClick={onShowDialog}>
              View All {assetBrowser.totalCount} Assets
            </Button>
          </div>
        )}

      {/* Error state */}
      {assetBrowser.error && !assetBrowser.loading && (
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
