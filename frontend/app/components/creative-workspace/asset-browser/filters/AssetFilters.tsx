import { useState } from "react";
import { AssetType, AssetFiltersProps } from "@/lib/types/assetBrowser";
import { useAssetCategories } from "@/hooks/useAssetBrowser";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Search, X, Filter } from "lucide-react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";

export function AssetFilters({
  selectedType,
  onTypeChange,
  selectedCategories,
  onCategoriesChange,
  searchQuery,
  onSearchChange,
  compact = false,
}: AssetFiltersProps) {
  const [showCategoryFilter, setShowCategoryFilter] = useState(false);

  // Use the established hook for category management
  const categories = useAssetCategories({
    assetType: selectedType,
    initialCategories: selectedCategories,
  });

  const handleCategoryToggle = (category: string) => {
    categories.toggleCategory(category);
    onCategoriesChange(categories.selectedCategories);
  };

  const clearAllFilters = () => {
    categories.clearCategories();
    onCategoriesChange([]);
    onSearchChange("");
  };

  // Get sorted categories (excluding 'all' and sorting by count)
  const sortedCategories = Object.entries(categories.categories)
    .filter(([category]) => category !== "all")
    .sort(([, countA], [, countB]) => (countB as number) - (countA as number))
    .slice(0, 20); // Limit to top 20 categories

  return (
    <div className="space-y-3">
      {/* Asset Type Tabs */}
      <Tabs
        value={selectedType}
        onValueChange={(value) => onTypeChange(value as AssetType)}
      >
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="hdris">HDRIs</TabsTrigger>
          <TabsTrigger value="textures">Textures</TabsTrigger>
          <TabsTrigger value="models">Models</TabsTrigger>
        </TabsList>
      </Tabs>

      {/* Search */}
      {!compact && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4" />
          <Input
            placeholder="Search assets..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10"
          />
          {searchQuery && (
            <Button
              variant="destructive"
              size="icon"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8"
              onClick={() => onSearchChange("")}
            >
              <X className="w-4 h-4" />
            </Button>
          )}
        </div>
      )}

      {/* Category Filter */}
      <div className="flex items-center gap-2">
        <Popover open={showCategoryFilter} onOpenChange={setShowCategoryFilter}>
          <PopoverTrigger asChild>
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
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={clearAllFilters}
                  >
                    Clear all
                  </Button>
                )}
              </div>

              {categories.loading ? (
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

        {/* Clear filters */}
        {(selectedCategories.length > 0 || searchQuery) && (
          <Button
            variant="destructive"
            size={compact ? "sm" : "default"}
            onClick={clearAllFilters}
          >
            <X className="w-4 h-4 mr-1" />
            Clear
          </Button>
        )}
      </div>

      {/* Selected Categories */}
      {selectedCategories.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {selectedCategories.map((category) => (
            <Badge
              key={category}
              className="bg-accent text-accent-foreground border-accent/30 pr-1"
            >
              {category}
              <Button
                variant="destructive"
                size="icon"
                className="h-4 w-4 ml-1"
                onClick={() => handleCategoryToggle(category)}
              >
                <X className="w-3 h-3" />
              </Button>
            </Badge>
          ))}
        </div>
      )}
    </div>
  );
}
