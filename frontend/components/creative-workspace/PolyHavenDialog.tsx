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
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from "@/components/ui/pagination";
import {
  AssetType,
  PolyHavenAsset,
  PaginatedAssetsResponse,
  polyhavenService,
  CategoriesResponse,
} from "@/lib/services/polyhavenService";
import { AssetGrid } from "./AssetGrid";
import {
  Search,
  X,
  Filter,
  Download,
  ExternalLink,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";

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
  const [assets, setAssets] = useState<Array<PolyHavenAsset & { id: string }>>(
    []
  );
  const [pagination, setPagination] = useState({
    page: 1,
    limit: 20,
    total_count: 0,
    total_pages: 0,
    has_next: false,
    has_prev: false,
  });
  const [selectedAsset, setSelectedAsset] = useState<
    (PolyHavenAsset & { id: string }) | undefined
  >(undefined);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | undefined>(undefined);
  const [categories, setCategories] = useState<CategoriesResponse>({});
  const [loadingCategories, setLoadingCategories] = useState(false);
  const [showCategoryFilter, setShowCategoryFilter] = useState(false);

  // Load categories when asset type changes
  useEffect(() => {
    const loadCategories = async () => {
      setLoadingCategories(true);
      try {
        const categoriesData =
          await polyhavenService.getCategories(selectedType);
        setCategories(categoriesData);
      } catch (error) {
        console.error("Failed to load categories:", error);
        setCategories({});
      } finally {
        setLoadingCategories(false);
      }
    };

    if (open) {
      loadCategories();
    }
  }, [open, selectedType]);

  // Load assets when filters change
  useEffect(() => {
    const loadAssets = async () => {
      setLoading(true);
      setError(undefined);
      try {
        const response = await polyhavenService.getAssetsPaginated({
          assetType: selectedType,
          categories:
            selectedCategories.length > 0 ? selectedCategories : undefined,
          page: 1,
          limit: 20,
          search: searchQuery.trim() || undefined,
        });

        const assetArray = polyhavenService.convertAssetsToArray(
          response.assets
        );
        setAssets(assetArray);
        setPagination(response.pagination);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load assets");
        setAssets([]);
        setPagination({
          page: 1,
          limit: 20,
          total_count: 0,
          total_pages: 0,
          has_next: false,
          has_prev: false,
        });
      } finally {
        setLoading(false);
      }
    };

    if (open) {
      loadAssets();
    }
  }, [open, selectedType, selectedCategories, searchQuery]);

  // Load more assets for pagination
  const loadPage = async (page: number) => {
    if (loading) return;

    setLoading(true);
    setError(undefined);
    try {
      const response = await polyhavenService.getAssetsPaginated({
        assetType: selectedType,
        categories:
          selectedCategories.length > 0 ? selectedCategories : undefined,
        page,
        limit: 20,
        search: searchQuery.trim() || undefined,
      });

      const assetArray = polyhavenService.convertAssetsToArray(response.assets);
      setAssets(assetArray);
      setPagination(response.pagination);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load assets");
    } finally {
      setLoading(false);
    }
  };

  // Since we're using server-side search, filteredAssets is just the current assets
  const filteredAssets = assets;

  const handleAssetSelect = (asset: PolyHavenAsset & { id: string }) => {
    setSelectedAsset(asset);
    onAssetSelect?.(asset);
  };

  const handleClose = () => {
    setSelectedAsset(undefined);
    onOpenChange(false);
  };

  const getAssetCount = () => {
    const currentPageCount = filteredAssets.length;
    const totalCount = pagination.total_count;

    if (searchQuery.trim() || selectedCategories.length > 0) {
      return `${currentPageCount} of ${totalCount} assets (Page ${pagination.page}/${pagination.total_pages})`;
    }
    return `${currentPageCount} of ${totalCount} assets (Page ${pagination.page}/${pagination.total_pages})`;
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-7xl h-[90vh] bg-cr8-charcoal border-white/10">
        <DialogHeader className="flex-shrink-0">
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
        </DialogHeader>

        <div className="relative min-h-0">
          {/* Horizontal Filters Row */}
          <div className="flex-shrink-0 flex items-center justify-between gap-4 mb-6">
            {/* Asset Type Tabs */}
            <Tabs
              value={selectedType}
              onValueChange={(value) => setSelectedType(value as AssetType)}
            >
              <TabsList className="bg-white/5 border border-white/10">
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

            {/* Search and Categories */}
            <div className="flex items-center gap-3">
              {/* Search Input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
                <Input
                  placeholder="Search assets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64 bg-white/5 border-white/10 text-white placeholder:text-white/40"
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

              {/* Categories Filter */}
              <Popover
                open={showCategoryFilter}
                onOpenChange={setShowCategoryFilter}
              >
                <PopoverTrigger asChild>
                  <Button
                    variant="outline"
                    className="border-white/20 bg-white/5 text-white hover:bg-white/10"
                  >
                    <Filter className="w-4 h-4 mr-2" />
                    Categories
                    {selectedCategories.length > 0 && (
                      <Badge className="ml-2 bg-primary/20 text-primary-foreground border-primary/30">
                        {selectedCategories.length}
                      </Badge>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80 bg-cr8-charcoal border-white/10">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium text-white">
                        Filter by Category
                      </h4>
                      {selectedCategories.length > 0 && (
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedCategories([])}
                          className="text-primary hover:text-primary-foreground"
                        >
                          Clear all
                        </Button>
                      )}
                    </div>

                    {loadingCategories ? (
                      <div className="grid grid-cols-2 gap-2">
                        {Array.from({ length: 8 }).map((_, i) => (
                          <div
                            key={i}
                            className="h-8 bg-gray-700 rounded animate-pulse"
                          />
                        ))}
                      </div>
                    ) : (
                      <div className="grid grid-cols-2 gap-2 max-h-60 overflow-y-auto">
                        {Object.entries(categories)
                          .filter(([category]) => category !== "all")
                          .sort(([, countA], [, countB]) => countB - countA)
                          .slice(0, 20)
                          .map(([category, count]) => (
                            <Button
                              key={category}
                              variant={
                                selectedCategories.includes(category)
                                  ? "default"
                                  : "outline"
                              }
                              size="sm"
                              className={`justify-between text-left ${
                                selectedCategories.includes(category)
                                  ? "bg-primary/20 text-primary-foreground border-primary/30"
                                  : "border-white/20 bg-white/5 text-white hover:bg-white/10"
                              }`}
                              onClick={() => {
                                const newCategories =
                                  selectedCategories.includes(category)
                                    ? selectedCategories.filter(
                                        (c) => c !== category
                                      )
                                    : [...selectedCategories, category];
                                setSelectedCategories(newCategories);
                              }}
                            >
                              <span className="truncate">{category}</span>
                              <Badge
                                variant="outline"
                                className="ml-1 text-xs border-white/20"
                              >
                                {count}
                              </Badge>
                            </Button>
                          ))}
                      </div>
                    )}
                  </div>
                </PopoverContent>
              </Popover>
            </div>
          </div>

          {/* Selected Categories */}
          {selectedCategories.length > 0 && (
            <div className="flex-shrink-0 flex flex-wrap gap-1 mb-6">
              {selectedCategories.map((category) => (
                <Badge
                  key={category}
                  className="bg-primary/20 text-primary-foreground border-primary/30 pr-1"
                >
                  {category}
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-4 w-4 ml-1 hover:bg-primary/30"
                    onClick={() => {
                      setSelectedCategories(
                        selectedCategories.filter((c) => c !== category)
                      );
                    }}
                  >
                    <X className="w-3 h-3" />
                  </Button>
                </Badge>
              ))}
            </div>
          )}

          {/* Asset Grid Container - Fixed to stay at top */}
          <div className="flex-1 min-h-0 pb-20">
            <div className="w-full max-w-6xl mx-auto">
              <AssetGrid
                assets={filteredAssets}
                onAssetSelect={handleAssetSelect}
                selectedAsset={selectedAsset}
                loading={loading}
                error={error}
              />
            </div>
          </div>

          {/* Centered Pagination - Always at bottom */}
          {pagination.total_pages > 1 && (
            <div className="absolute bottom-0 left-0 right-0 flex-shrink-0 flex justify-center mt-6">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      onClick={() =>
                        pagination.has_prev && loadPage(pagination.page - 1)
                      }
                      className={`border-white/20 bg-white/5 text-white hover:bg-white/10 ${
                        !pagination.has_prev || loading
                          ? "opacity-50 cursor-not-allowed"
                          : "cursor-pointer"
                      }`}
                    />
                  </PaginationItem>

                  {Array.from(
                    { length: Math.min(5, pagination.total_pages) },
                    (_, i) => {
                      const startPage = Math.max(1, pagination.page - 2);
                      const pageNum = startPage + i;

                      if (pageNum > pagination.total_pages) return null;

                      return (
                        <PaginationItem key={pageNum}>
                          <PaginationLink
                            onClick={() => loadPage(pageNum)}
                            isActive={pageNum === pagination.page}
                            className={`cursor-pointer ${
                              pageNum === pagination.page
                                ? "bg-primary hover:bg-primary/80 text-white border-primary"
                                : "border-white/20 bg-white/5 text-white hover:bg-white/10"
                            } ${loading ? "opacity-50 cursor-not-allowed" : ""}`}
                          >
                            {pageNum}
                          </PaginationLink>
                        </PaginationItem>
                      );
                    }
                  )}

                  {pagination.total_pages > 5 &&
                    pagination.page < pagination.total_pages - 2 && (
                      <>
                        <PaginationItem>
                          <PaginationEllipsis className="text-white/60" />
                        </PaginationItem>
                        <PaginationItem>
                          <PaginationLink
                            onClick={() => loadPage(pagination.total_pages)}
                            className="cursor-pointer border-white/20 bg-white/5 text-white hover:bg-white/10"
                          >
                            {pagination.total_pages}
                          </PaginationLink>
                        </PaginationItem>
                      </>
                    )}

                  <PaginationItem>
                    <PaginationNext
                      onClick={() =>
                        pagination.has_next && loadPage(pagination.page + 1)
                      }
                      className={`border-white/20 bg-white/5 text-white hover:bg-white/10 ${
                        !pagination.has_next || loading
                          ? "opacity-50 cursor-not-allowed"
                          : "cursor-pointer"
                      }`}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
