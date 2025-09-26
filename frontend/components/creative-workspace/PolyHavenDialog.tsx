import { useState, useEffect, useMemo } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import {
  AssetType,
  PolyHavenAsset,
  polyhavenService,
} from "@/lib/services/polyhavenService";
import { AssetGrid } from "./AssetGrid";
import { AssetFilters } from "./AssetFilters";
import { Search, X, ExternalLink, Download } from "lucide-react";

interface PolyHavenDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  initialType?: AssetType;
}

export function PolyHavenDialog({
  open,
  onOpenChange,
  onAssetSelect,
  initialType = "textures",
}: PolyHavenDialogProps) {
  const [selectedType, setSelectedType] = useState<AssetType>(initialType);
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [assets, setAssets] = useState<Record<string, PolyHavenAsset>>({});
  const [selectedAsset, setSelectedAsset] = useState<
    (PolyHavenAsset & { id: string }) | undefined
  >(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);

  // Load assets when filters change
  useEffect(() => {
    const loadAssets = async () => {
      setLoading(true);
      setError(undefined);
      try {
        const assetsData = await polyhavenService.getAssets(
          selectedType,
          selectedCategories.length > 0 ? selectedCategories : undefined
        );
        setAssets(assetsData);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load assets");
        setAssets({});
      } finally {
        setLoading(false);
      }
    };

    if (open) {
      loadAssets();
    }
  }, [open, selectedType, selectedCategories]);

  // Filter assets by search query
  const filteredAssets = useMemo(() => {
    const assetArray = polyhavenService.convertAssetsToArray(assets);

    if (!searchQuery.trim()) {
      return assetArray;
    }

    const query = searchQuery.toLowerCase().trim();
    return assetArray.filter(
      (asset) =>
        asset.name.toLowerCase().includes(query) ||
        asset.categories.some((cat) => cat.toLowerCase().includes(query)) ||
        asset.tags.some((tag) => tag.toLowerCase().includes(query)) ||
        Object.keys(asset.authors).some((author) =>
          author.toLowerCase().includes(query)
        )
    );
  }, [assets, searchQuery]);

  const handleAssetSelect = (asset: PolyHavenAsset & { id: string }) => {
    setSelectedAsset(asset);
    onAssetSelect?.(asset);
  };

  const handleClose = () => {
    setSelectedAsset(undefined);
    onOpenChange(false);
  };

  const getAssetCount = () => {
    const total = Object.keys(assets).length;
    const filtered = filteredAssets.length;

    if (searchQuery.trim() || selectedCategories.length > 0) {
      return `${filtered} of ${total} assets`;
    }
    return `${total} assets`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-7xl h-[90vh] bg-cr8-charcoal border-white/10">
        <DialogHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {/* Poly Haven Logo */}
              <div className="flex items-center gap-2">
                <img
                  src="/assets/polyhaven_256.png"
                  alt="Poly Haven"
                  className="w-8 h-8"
                />
                <DialogTitle className="text-2xl font-bold text-white">
                  Poly Haven Assets
                </DialogTitle>
              </div>
              <Badge className="bg-orange-500/20 text-orange-300 border-orange-500/30">
                {getAssetCount()}
              </Badge>
            </div>

            <div className="flex items-center gap-2">
              <Button
                variant="outline"
                size="sm"
                className="border-white/20 bg-white/5 text-white hover:bg-white/10"
                onClick={() => window.open("https://polyhaven.com", "_blank")}
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Visit Poly Haven
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 flex gap-6 min-h-0">
          {/* Filters Sidebar */}
          <div className="w-80 flex-shrink-0 space-y-4">
            <AssetFilters
              selectedType={selectedType}
              onTypeChange={setSelectedType}
              selectedCategories={selectedCategories}
              onCategoriesChange={setSelectedCategories}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
            />

            {/* Asset Info Panel */}
            {selectedAsset && (
              <div className="bg-white/5 border border-white/10 rounded-lg p-4 space-y-3">
                <h3 className="font-medium text-white text-lg">
                  {selectedAsset.name}
                </h3>

                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-white/60">Type:</span>
                    <span className="text-white">
                      {polyhavenService.getAssetTypeDisplayName(
                        polyhavenService.getAssetTypeFromNumber(
                          selectedAsset.type
                        )
                      )}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-white/60">Downloads:</span>
                    <span className="text-white">
                      {selectedAsset.download_count.toLocaleString()}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span className="text-white/60">Resolution:</span>
                    <span className="text-white">
                      {selectedAsset.max_resolution.join(" × ")}
                    </span>
                  </div>
                </div>

                <div>
                  <div className="text-white/60 text-sm mb-2">Authors:</div>
                  <div className="space-y-1">
                    {Object.entries(selectedAsset.authors).map(
                      ([author, role]) => (
                        <div key={author} className="text-sm">
                          <span className="text-white">{author}</span>
                          <span className="text-white/60 ml-2">({role})</span>
                        </div>
                      )
                    )}
                  </div>
                </div>

                <div>
                  <div className="text-white/60 text-sm mb-2">Categories:</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedAsset.categories.map((category) => (
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

                <div className="pt-2 space-y-2">
                  <Button
                    className="w-full bg-orange-500 hover:bg-orange-600 text-white"
                    onClick={() => {
                      onAssetSelect?.(selectedAsset);
                      handleClose();
                    }}
                  >
                    <Download className="w-4 h-4 mr-2" />
                    Use Asset
                  </Button>

                  <Button
                    variant="outline"
                    className="w-full border-white/20 bg-white/5 text-white hover:bg-white/10"
                    onClick={() =>
                      window.open(
                        `https://polyhaven.com/a/${selectedAsset.id}`,
                        "_blank"
                      )
                    }
                  >
                    <ExternalLink className="w-4 h-4 mr-2" />
                    View Details
                  </Button>
                </div>
              </div>
            )}
          </div>

          {/* Asset Grid */}
          <div className="flex-1 overflow-y-auto">
            <AssetGrid
              assets={filteredAssets}
              onAssetSelect={handleAssetSelect}
              selectedAsset={selectedAsset}
              loading={loading}
              error={error}
            />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
