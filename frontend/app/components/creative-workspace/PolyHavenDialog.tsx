import { useState, useEffect } from "react";
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
  polyhavenService,
  CategoriesResponse,
} from "@/lib/services/polyhavenService";
import { AssetGrid } from "./AssetGrid";
import { Search, X, Filter } from "lucide-react";
import polyhaveLogo from "@/assets/polyhaven_256.png";

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
    onAssetSelect?.(asset);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-7xl! h-[90vh]!">
        <DialogHeader className="shrink-0">
          <div className="flex items-center gap-2">
            <img src={polyhaveLogo} alt="Poly Haven" className="w-8 h-8" />
            <DialogTitle>Poly Haven Assets</DialogTitle>
          </div>
        </DialogHeader>

        <div className="relative min-h-0">
          {/* Horizontal Filters Row */}
          <div className="shrink-0 flex items-center justify-between gap-4 mb-6">
            {/* Asset Type Tabs */}
            <Tabs
              value={selectedType}
              onValueChange={(value) => setSelectedType(value as AssetType)}
            >
              <TabsList>
                <TabsTrigger value="hdris">HDRIs</TabsTrigger>
                <TabsTrigger value="textures">Textures</TabsTrigger>
                <TabsTrigger value="models">Models</TabsTrigger>
              </TabsList>
            </Tabs>

            {/* Search and Categories */}
            <div className="flex items-center gap-3">
              {/* Search Input */}
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-muted-foreground" />
                <Input
                  placeholder="Search assets..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 w-64"
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

              {/* Categories Filter */}
              <Popover
                open={showCategoryFilter}
                onOpenChange={setShowCategoryFilter}
              >
                <PopoverTrigger>
                  <Button variant="outline">
                    <Filter className="w-4 h-4 mr-2" />
                    Categories
                    {selectedCategories.length > 0 && (
                      <Badge className="ml-2 bg-primary/20 text-primary-foreground border-primary/30">
                        {selectedCategories.length}
                      </Badge>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">Filter by Category</h4>
                      {selectedCategories.length > 0 && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => setSelectedCategories([])}
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
                            className="h-8 bg-secondary rounded animate-pulse"
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
                              className={`justify-between text-left`}
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
                              <Badge variant="outline" className="ml-1 text-xs">
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
            <div className="shrink-0 flex flex-wrap gap-1 mb-6">
              {selectedCategories.map((category) => (
                <Badge
                  key={category}
                  className="bg-primary/20 text-primary-foreground border-primary/30 pr-1"
                >
                  {category}
                  <Button
                    variant="destructive"
                    size="icon"
                    className="h-4 w-4 ml-1"
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
                loading={loading}
                error={error}
              />
            </div>
          </div>

          {/* Centered Pagination - Always at bottom */}
          {pagination.total_pages > 1 && (
            <div className="absolute bottom-0 left-0 right-0 shrink-0 flex justify-center mt-6">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      size="default"
                      onClick={() =>
                        pagination.has_prev &&
                        !loading &&
                        loadPage(pagination.page - 1)
                      }
                      className={
                        !pagination.has_prev || loading
                          ? "pointer-events-none opacity-50"
                          : ""
                      }
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
                            size="icon"
                            onClick={() => !loading && loadPage(pageNum)}
                            isActive={pageNum === pagination.page}
                            className={
                              loading ? "pointer-events-none opacity-50" : ""
                            }
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
                          <PaginationEllipsis />
                        </PaginationItem>
                        <PaginationItem>
                          <PaginationLink
                            size="icon"
                            onClick={() =>
                              !loading && loadPage(pagination.total_pages)
                            }
                            className={
                              loading ? "pointer-events-none opacity-50" : ""
                            }
                          >
                            {pagination.total_pages}
                          </PaginationLink>
                        </PaginationItem>
                      </>
                    )}

                  <PaginationItem>
                    <PaginationNext
                      size="default"
                      onClick={() =>
                        pagination.has_next &&
                        !loading &&
                        loadPage(pagination.page + 1)
                      }
                      className={
                        !pagination.has_next || loading
                          ? "pointer-events-none opacity-50"
                          : ""
                      }
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
