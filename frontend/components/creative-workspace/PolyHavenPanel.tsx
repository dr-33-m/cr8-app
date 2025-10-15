import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { RefreshCw, Search, X } from "lucide-react";
import {
  AssetType,
  PolyHavenAsset,
  polyhavenService,
} from "@/lib/services/polyhavenService";
import { AssetGrid } from "./AssetGrid";
import { PolyHavenDialog } from "./PolyHavenDialog";

interface PolyHavenPanelProps {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
}

export function PolyHavenPanel({ onAssetSelect }: PolyHavenPanelProps) {
  const [selectedType, setSelectedType] = useState<AssetType>("textures");
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
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
              <Badge className="bg-primary/20 text-white border-primary/30 text-xs">
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

        {/* Asset Type Tabs */}
        <Tabs
          value={selectedType}
          onValueChange={(value) => setSelectedType(value as AssetType)}
        >
          <TabsList className="grid w-full grid-cols-3 bg-white/5 border border-white/10">
            <TabsTrigger
              value="hdris"
              className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-300"
            >
              HDRIs
            </TabsTrigger>
            <TabsTrigger
              value="textures"
              className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-300"
            >
              Textures
            </TabsTrigger>
            <TabsTrigger
              value="models"
              className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300"
            >
              Models
            </TabsTrigger>
          </TabsList>
        </Tabs>

        {/* Compact Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
          <Input
            placeholder="Search preview assets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 text-white/40 hover:text-white"
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
