import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CardContent } from "@/components/ui/card";
import { RefreshCw, Search, X } from "lucide-react";
import { PolyHavenAsset, AssetType } from "@/lib/services/polyhavenService";
import { useAssetBrowser } from "@/hooks/useAssetBrowser";
import { AssetGrid } from "../assets/AssetGrid";
import { PolyHavenDialog } from "./dialogue/PolyHavenDialog";
import { ErrorComponent } from "@/components/errors/ErrorComponent";
import polyhaveLogo from "@/assets/polyhaven_256.png";

interface PolyHavenPanelProps {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
}

export function PolyHavenPanel({ onAssetSelect }: PolyHavenPanelProps) {
  const [dialogOpen, setDialogOpen] = useState(false);

  // Use the asset browser hook with compact view settings
  const assetBrowser = useAssetBrowser({
    initialType: "textures",
    initialLimit: 6, // Limit to 6 for compact view
    onAssetSelect,
  });

  const handleRefresh = () => {
    assetBrowser.refresh();
  };

  // Get limited assets for compact view
  const limitedAssets = assetBrowser.getLimitedAssets(6);

  return (
    <>
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

        {/* Asset Type Tabs */}
        <Tabs
          value={assetBrowser.selectedType}
          onValueChange={(value) => assetBrowser.setType(value as AssetType)}
        >
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="hdris">HDRIs</TabsTrigger>
            <TabsTrigger value="textures">Textures</TabsTrigger>
            <TabsTrigger value="models">Models</TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Compact Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" />
          <Input
            placeholder="Search preview assets..."
            value={assetBrowser.searchQuery}
            onChange={(e) => assetBrowser.setSearch(e.target.value)}
            className="pl-10"
          />
          {assetBrowser.searchQuery && (
            <Button
              variant="destructive"
              size="icon"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8"
              onClick={() => assetBrowser.clearSearch()}
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>

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
              <Button
                variant="outline"
                size="sm"
                onClick={() => setDialogOpen(true)}
              >
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

      {/* Expanded Dialog */}
      <PolyHavenDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onAssetSelect={onAssetSelect}
        initialType={assetBrowser.selectedType}
      />
    </>
  );
}
