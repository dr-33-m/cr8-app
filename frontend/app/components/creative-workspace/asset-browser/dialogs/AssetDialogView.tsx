import { useState } from "react";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
  PaginationEllipsis,
} from "@/components/ui/pagination";
import { useAssetBrowser } from "@/hooks/useAssetBrowser";
import { AssetGrid } from "../grids";
import {
  AssetTypeTabs,
  AssetSearchInput,
  CategoryFilterPopover,
  SelectedCategoriesDisplay,
} from "../filters";
import { AssetDialogViewProps } from "@/lib/types/assetBrowser";

export function AssetDialogView({
  onAssetSelect,
  initialType = "textures",
}: AssetDialogViewProps) {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  // Use asset browser hook with dialog settings
  const assetBrowser = useAssetBrowser({
    initialType,
    initialLimit: 20, // Full pagination for dialog
    onAssetSelect,
    enabled: true, // Always enabled for dialog
  });

  // Handle pagination
  const handlePageChange = (page: number) => {
    assetBrowser.setPage(page);
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

  // Since we're using server-side search, filteredAssets is just current assets
  const filteredAssets = assetBrowser.assets;

  return (
    <div className="relative min-h-0">
      {/* Horizontal Filters Row */}
      <div className="shrink-0 flex items-center justify-between gap-4 mb-6">
        {/* Asset Type Tabs - Left side */}
        <AssetTypeTabs
          selectedType={assetBrowser.selectedType}
          onTypeChange={handleTypeChange}
        />

        {/* Search and Category Filters - Right side */}
        <div className="flex items-center gap-3">
          <AssetSearchInput
            value={assetBrowser.searchQuery}
            onChange={handleSearchChange}
            onClear={handleSearchClear}
            placeholder="Search assets..."
          />
          <CategoryFilterPopover
            selectedCategories={selectedCategories}
            onCategoriesChange={handleCategoriesChange}
            assetType={assetBrowser.selectedType}
          />
        </div>
      </div>

      {/* Selected Categories Display */}
      {selectedCategories.length > 0 && (
        <div className="shrink-0 flex flex-wrap gap-1 mb-6">
          <SelectedCategoriesDisplay
            selectedCategories={selectedCategories}
            onCategoryRemove={(category) => {
              const updated = selectedCategories.filter((c) => c !== category);
              handleCategoriesChange(updated);
            }}
            onClearAll={() => handleCategoriesChange([])}
          />
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

                  if (pageNum > assetBrowser.pagination.totalPages) return null;

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
                          handlePageChange(assetBrowser.pagination.totalPages)
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
  );
}
