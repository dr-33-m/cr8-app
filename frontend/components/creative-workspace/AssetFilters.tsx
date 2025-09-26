import { useState, useEffect } from "react";
import {
  AssetType,
  polyhavenService,
  CategoriesResponse,
} from "@/lib/services/polyhavenService";
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

interface AssetFiltersProps {
  selectedType: AssetType;
  onTypeChange: (type: AssetType) => void;
  selectedCategories: string[];
  onCategoriesChange: (categories: string[]) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  compact?: boolean;
}

export function AssetFilters({
  selectedType,
  onTypeChange,
  selectedCategories,
  onCategoriesChange,
  searchQuery,
  onSearchChange,
  compact = false,
}: AssetFiltersProps) {
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

    loadCategories();
  }, [selectedType]);

  const handleCategoryToggle = (category: string) => {
    const newCategories = selectedCategories.includes(category)
      ? selectedCategories.filter((c) => c !== category)
      : [...selectedCategories, category];
    onCategoriesChange(newCategories);
  };

  const clearAllFilters = () => {
    onCategoriesChange([]);
    onSearchChange("");
  };

  // Get sorted categories (excluding 'all' and sorting by count)
  const sortedCategories = Object.entries(categories)
    .filter(([category]) => category !== "all")
    .sort(([, countA], [, countB]) => countB - countA)
    .slice(0, 20); // Limit to top 20 categories

  return (
    <div className="space-y-3">
      {/* Asset Type Tabs */}
      <Tabs
        value={selectedType}
        onValueChange={(value) => onTypeChange(value as AssetType)}
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

      {/* Search */}
      {!compact && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-white/40" />
          <Input
            placeholder="Search assets..."
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            className="pl-10 bg-white/5 border-white/10 text-white placeholder:text-white/40"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="icon"
              className="absolute right-1 top-1/2 transform -translate-y-1/2 h-8 w-8 text-white/40 hover:text-white"
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
            <Button
              variant="outline"
              size={compact ? "sm" : "default"}
              className="border-white/20 bg-white/5 text-white hover:bg-white/10"
            >
              <Filter className="w-4 h-4 mr-2" />
              Categories
              {selectedCategories.length > 0 && (
                <Badge className="ml-2 bg-orange-500/20 text-orange-300 border-orange-500/30">
                  {selectedCategories.length}
                </Badge>
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-80 bg-cr8-charcoal border-white/10">
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="font-medium text-white">Filter by Category</h4>
                {selectedCategories.length > 0 && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={clearAllFilters}
                    className="text-orange-400 hover:text-orange-300"
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
                  {sortedCategories.map(([category, count]) => (
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
                          ? "bg-orange-500/20 text-orange-300 border-orange-500/30"
                          : "border-white/20 bg-white/5 text-white hover:bg-white/10"
                      }`}
                      onClick={() => handleCategoryToggle(category)}
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

        {/* Clear filters */}
        {(selectedCategories.length > 0 || searchQuery) && (
          <Button
            variant="ghost"
            size={compact ? "sm" : "default"}
            onClick={clearAllFilters}
            className="text-orange-400 hover:text-orange-300"
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
              className="bg-orange-500/20 text-orange-300 border-orange-500/30 pr-1"
            >
              {category}
              <Button
                variant="ghost"
                size="icon"
                className="h-4 w-4 ml-1 hover:bg-orange-500/30"
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
