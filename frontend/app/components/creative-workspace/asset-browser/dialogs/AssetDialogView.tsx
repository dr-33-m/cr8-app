import { useState } from "react";
import {
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationNext,
  PaginationPrevious,
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
import { PaginationPages } from "../pagination";

export const DIALOG_ASSETS_PER_PAGE = 20;
export const MAX_VISIBLE_PAGES = 5;

export function AssetDialogView({
  onAssetSelect,
  initialType = "textures",
}: AssetDialogViewProps) {
  const [selectedCategories, setSelectedCategories] = useState<string[]>([]);

  const assetBrowser = useAssetBrowser({
    initialType,
    initialLimit: DIALOG_ASSETS_PER_PAGE,
    onAssetSelect,
    enabled: true,
  });

  const {
    assets,
    selectedType,
    searchQuery,
    loading,
    error,
    pagination,
    setType,
    setSearch,
    clearSearch,
    setCategories,
    setPage,
    selectAsset,
  } = assetBrowser;

  const handleCategoriesChange = (categories: string[]) => {
    setSelectedCategories(categories);
    setCategories(categories);
  };

  const handleCategoryRemove = (category: string) => {
    const updated = selectedCategories.filter((c) => c !== category);
    handleCategoriesChange(updated);
  };

  const handlePageClick = (pageNum: number) => {
    if (!loading) setPage(pageNum);
  };

  return (
    <div className="relative min-h-0">
      {/* Filters Row */}
      <div className="shrink-0 flex items-center justify-between gap-4 mb-6">
        <AssetTypeTabs selectedType={selectedType} onTypeChange={setType} />

        <div className="flex items-center gap-3">
          <AssetSearchInput
            value={searchQuery}
            onChange={setSearch}
            onClear={clearSearch}
            placeholder="Search assets..."
          />
          <CategoryFilterPopover
            selectedCategories={selectedCategories}
            onCategoriesChange={handleCategoriesChange}
            assetType={selectedType}
          />
        </div>
      </div>

      {/* Selected Categories */}
      {selectedCategories.length > 0 && (
        <div className="shrink-0 flex flex-wrap gap-1 mb-6">
          <SelectedCategoriesDisplay
            selectedCategories={selectedCategories}
            onCategoryRemove={handleCategoryRemove}
            onClearAll={() => handleCategoriesChange([])}
          />
        </div>
      )}

      {/* Asset Grid */}
      <div className="flex-1 min-h-0 pb-20">
        <div className="w-full max-w-6xl mx-auto">
          <AssetGrid
            assets={assets}
            onAssetSelect={selectAsset}
            loading={loading}
            error={error}
          />
        </div>
      </div>

      {/* Pagination */}
      {pagination.totalPages > 1 && (
        <div className="absolute bottom-0 left-0 right-0 shrink-0 flex justify-center mt-6">
          <Pagination>
            <PaginationContent>
              <PaginationItem>
                <PaginationPrevious
                  size="default"
                  onClick={() =>
                    pagination.hasPrev &&
                    !loading &&
                    handlePageClick(pagination.page - 1)
                  }
                  className={
                    !pagination.hasPrev || loading
                      ? "pointer-events-none opacity-50"
                      : ""
                  }
                />
              </PaginationItem>

              <PaginationPages
                currentPage={pagination.page}
                totalPages={pagination.totalPages}
                loading={loading}
                onPageClick={handlePageClick}
              />

              <PaginationItem>
                <PaginationNext
                  size="default"
                  onClick={() =>
                    pagination.hasNext &&
                    !loading &&
                    handlePageClick(pagination.page + 1)
                  }
                  className={
                    !pagination.hasNext || loading
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
