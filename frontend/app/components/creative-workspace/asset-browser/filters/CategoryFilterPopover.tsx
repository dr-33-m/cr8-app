import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Filter } from "lucide-react";
import { useAssetCategories } from "@/hooks/useAssetBrowser";
import { CategoryFilterPopoverProps } from "@/lib/types/assetBrowser";

export function CategoryFilterPopover({
  selectedCategories,
  onCategoriesChange,
  assetType,
  compact = false,
  categories: providedCategories,
  loading: providedLoading,
}: CategoryFilterPopoverProps) {
  const [showCategoryFilter, setShowCategoryFilter] = useState(false);

  // Use the established hook for category management if not provided
  const categoriesHook = useAssetCategories({
    assetType,
    initialCategories: selectedCategories,
  });

  // Use provided categories or fall back to hook
  const categories = providedCategories || categoriesHook.categories;
  const loading =
    providedLoading !== undefined ? providedLoading : categoriesHook.loading;

  const handleCategoryToggle = (category: string) => {
    const newCategories = selectedCategories.includes(category)
      ? selectedCategories.filter((c) => c !== category)
      : [...selectedCategories, category];
    onCategoriesChange(newCategories);
  };

  const clearAllFilters = () => {
    onCategoriesChange([]);
  };

  // Get sorted categories (excluding 'all' and sorting by count)
  const sortedCategories = Object.entries(categories)
    .filter(([category]) => category !== "all")
    .sort(([, countA], [, countB]) => countB - countA)
    .slice(0, 20); // Limit to top 20 categories

  return (
    <Popover open={showCategoryFilter} onOpenChange={setShowCategoryFilter}>
      <PopoverTrigger>
        <Button variant="outline" size={compact ? "sm" : "default"}>
          <Filter className="w-4 h-4 mr-2" />
          Categories
          {selectedCategories.length > 0 && (
            <Badge className="ml-2 bg-accent text-accent-foreground border-accent/30">
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
              <Button variant="destructive" size="sm" onClick={clearAllFilters}>
                Clear all
              </Button>
            )}
          </div>

          {loading ? (
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
              {sortedCategories.map(([category, count]) => (
                <Button
                  key={category}
                  variant={
                    selectedCategories.includes(category)
                      ? "default"
                      : "outline"
                  }
                  size="sm"
                  className={`justify-between text-left`}
                  onClick={() => handleCategoryToggle(category)}
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
  );
}
