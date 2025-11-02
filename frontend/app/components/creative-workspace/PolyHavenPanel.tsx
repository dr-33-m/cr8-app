import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { CardContent } from "@/components/ui/card";
import { RefreshCw, Search, X } from "lucide-react";
import {
  AssetType,
  PolyHavenAsset,
  polyhavenService,
} from "@/lib/services/polyhavenService";
import { AssetGrid } from "./AssetGrid";
import { PolyHavenDialog } from "./PolyHavenDialog";
import { ErrorComponent } from "@/components/errors/ErrorComponent";
import polyhaveLogo from "@/assets/polyhaven_256.png";

interface PolyHavenPanelProps {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
}

export function PolyHavenPanel({ onAssetSelect }: PolyHavenPanelProps) {
  const [selectedType, setSelectedType] = useState<AssetType>("textures");
  const [searchQuery, setSearchQuery] = useState("");
  const [assets, setAssets] = useState<Array<PolyHavenAsset & { id: string }>>(
    []
  );
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [dialogOpen, setDialogOpen] = useState(false);

  // Load assets based on type and search query
  useEffect(() => {
    const loadAssets = async () => {
      setLoading(true);
      setError(undefined);
      try {
        if (searchQuery.trim()) {
          // Use server-side search when there's a query
          const response = await polyhavenService.getAssetsPaginated({
            assetType: selectedType,
            search: searchQuery.trim(),
            page: 1,
            limit: 6,
          });
          const assetArray = polyhavenService.convertAssetsToArray(
            response.assets
          );
          setAssets(assetArray);
          setTotalCount(response.pagination.total_count);
        } else {
          // Load first 20 assets when no search query
          const response = await polyhavenService.getAssets(selectedType);
          const assetArray = polyhavenService.convertAssetsToArray(
            response.assets
          );
          setAssets(assetArray);
          setTotalCount(response.pagination.total_count);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load assets");
        setAssets([]);
        setTotalCount(0);
      } finally {
        setLoading(false);
      }
    };

    loadAssets();
  }, [selectedType, searchQuery]);

  const handleAssetSelect = (asset: PolyHavenAsset & { id: string }) => {
    onAssetSelect?.(asset);
  };

  const handleRefresh = async () => {
    setLoading(true);
    setError(undefined);
    try {
      const response = await polyhavenService.getAssets(selectedType);
      const assetArray = polyhavenService.convertAssetsToArray(response.assets);
      setAssets(assetArray);
      setTotalCount(response.pagination.total_count);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load assets");
    } finally {
      setLoading(false);
    }
  };

  // Get limited assets for compact view (first 6) - no client filtering needed since server already filtered
  const limitedAssets = assets.slice(0, 6);

  const getAssetCount = () => {
    return totalCount;
  };

  return (
    <>
      <CardContent className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src={polyhaveLogo} alt="Poly Haven" className="w-6 h-6" />
            <h3 className="text-lg font-medium">Poly Haven</h3>
            {!loading && (
              <Badge className="bg-primary/20 text-primary-foreground white border-primary/30 text-xs">
                {getAssetCount()}
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw
                className={`h-4 w-4 ${loading ? "animate-spin" : ""}`}
              />
            </Button>
          </div>
        </div>

        {/* Asset Type Tabs */}
        <Tabs
          value={selectedType}
          onValueChange={(value) => setSelectedType(value as AssetType)}
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
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
          {searchQuery && (
            <Button
              variant="destructive"
              size="icon"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8"
              onClick={() => setSearchQuery("")}
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>

        {/* Asset Grid */}
        <AssetGrid
          assets={limitedAssets}
          onAssetSelect={handleAssetSelect}
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
              onClick={() => setDialogOpen(true)}
            >
              View All {getAssetCount()} Assets
            </Button>
          </div>
        )}

        {/* Error state */}
        {error && !loading && (
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
        initialType={selectedType}
      />
    </>
  );
}
