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
import { AssetType, PolyHavenAsset } from "@/lib/services/polyhavenService";
import { Search, X, Filter } from "lucide-react";
import polyhaveLogo from "@/assets/polyhaven_256.png";
import { useAssetBrowser } from "@/hooks/useAssetBrowser";
import { AssetGrid } from "../../assets/AssetGrid";

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
  const [showCategoryFilter, setShowCategoryFilter] = useState(false);

  // Use the asset browser hook with dialog settings
  const assetBrowser = useAssetBrowser({
    initialType,
    initialLimit: 20, // Full pagination for dialog
    onAssetSelect,
    enabled: open, // Only enable when dialog is open
  });

  // Reset to initial type when dialog opens
  useEffect(() => {
    if (open) {
      assetBrowser.setType(initialType);
    }
  }, [open, initialType]);

  // Handle pagination
  const handlePageChange = (page: number) => {
    assetBrowser.setPage(page);
  };

  // Since we're using server-side search, filteredAssets is just the current assets
  const filteredAssets = assetBrowser.assets;

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
              value={assetBrowser.selectedType}
              onValueChange={(value) =>
                assetBrowser.setType(value as AssetType)
              }
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
                  value={assetBrowser.searchQuery}
                  onChange={(e) => assetBrowser.setSearch(e.target.value)}
                  className="pl-10 w-64"
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

              {/* Categories Filter */}
              <Popover
                open={showCategoryFilter}
                onOpenChange={setShowCategoryFilter}
              >
                <PopoverTrigger>
                  <Button variant="outline">
                    <Filter className="w-4 h-4 mr-2" />
                    Categories
                    {assetBrowser.selectedCategories.length > 0 && (
                      <Badge className="ml-2 bg-primary/20 text-primary-foreground border-primary/30">
                        {assetBrowser.selectedCategories.length}
                      </Badge>
                    )}
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <h4 className="font-medium">Filter by Category</h4>
                      {assetBrowser.selectedCategories.length > 0 && (
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => assetBrowser.clearCategories()}
                        >
                          Clear all
                        </Button>
                      )}
                    </div>

                    {assetBrowser.loading ? (
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
                        {Object.entries(assetBrowser.categories)
                          .filter(([category]) => category !== "all")
                          .sort(
                            ([, countA], [, countB]) =>
                              (countB as number) - (countA as number)
                          )
                          .slice(0, 20)
                          .map(([category, count]) => (
                            <Button
                              key={category}
                              variant={
                                assetBrowser.selectedCategories.includes(
                                  category
                                )
                                  ? "default"
                                  : "outline"
                              }
                              size="sm"
                              className={`justify-between text-left`}
                              onClick={() =>
                                assetBrowser.toggleCategory(category)
                              }
                            >
                              <span className="truncate">{category}</span>
                              <Badge variant="outline" className="ml-1 text-xs">
                                {count as number}
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
          {assetBrowser.selectedCategories.length > 0 && (
            <div className="shrink-0 flex flex-wrap gap-1 mb-6">
              {assetBrowser.selectedCategories.map((category) => (
                <Badge
                  key={category}
                  className="bg-primary/20 text-primary-foreground border-primary/30 pr-1"
                >
                  {category}
                  <Button
                    variant="destructive"
                    size="icon"
                    className="h-4 w-4 ml-1"
                    onClick={() => assetBrowser.removeCategory(category)}
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
                onAssetSelect={assetBrowser.selectAsset}
                loading={assetBrowser.loading}
                error={assetBrowser.error}
              />
            </div>
          </div>

          {/* Centered Pagination - Always at bottom */}
          {assetBrowser.pagination.totalPages > 1 && (
            <div className="absolute bottom-0 left-0 right-0 shrink-0 flex justify-center mt-6">
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious
                      size="default"
                      onClick={() =>
                        assetBrowser.pagination.hasPrev &&
                        !assetBrowser.loading &&
                        handlePageChange(assetBrowser.pagination.page - 1)
                      }
                      className={
                        !assetBrowser.pagination.hasPrev || assetBrowser.loading
                          ? "pointer-events-none opacity-50"
                          : ""
                      }
                    />
                  </PaginationItem>

                  {Array.from(
                    { length: Math.min(5, assetBrowser.pagination.totalPages) },
                    (_, i) => {
                      const startPage = Math.max(
                        1,
                        assetBrowser.pagination.page - 2
                      );
                      const pageNum = startPage + i;

                      if (pageNum > assetBrowser.pagination.totalPages)
                        return null;

                      return (
                        <PaginationItem key={pageNum}>
                          <PaginationLink
                            size="icon"
                            onClick={() =>
                              !assetBrowser.loading && handlePageChange(pageNum)
                            }
                            isActive={pageNum === assetBrowser.pagination.page}
                            className={
                              assetBrowser.loading
                                ? "pointer-events-none opacity-50"
                                : ""
                            }
                          >
                            {pageNum}
                          </PaginationLink>
                        </PaginationItem>
                      );
                    }
                  )}

                  {assetBrowser.pagination.totalPages > 5 &&
                    assetBrowser.pagination.page <
                      assetBrowser.pagination.totalPages - 2 && (
                      <>
                        <PaginationItem>
                          <PaginationEllipsis />
                        </PaginationItem>
                        <PaginationItem>
                          <PaginationLink
                            size="icon"
                            onClick={() =>
                              !assetBrowser.loading &&
                              handlePageChange(
                                assetBrowser.pagination.totalPages
                              )
                            }
                            className={
                              assetBrowser.loading
                                ? "pointer-events-none opacity-50"
                                : ""
                            }
                          >
                            {assetBrowser.pagination.totalPages}
                          </PaginationLink>
                        </PaginationItem>
                      </>
                    )}

                  <PaginationItem>
                    <PaginationNext
                      size="default"
                      onClick={() =>
                        assetBrowser.pagination.hasNext &&
                        !assetBrowser.loading &&
                        handlePageChange(assetBrowser.pagination.page + 1)
                      }
                      className={
                        !assetBrowser.pagination.hasNext || assetBrowser.loading
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
