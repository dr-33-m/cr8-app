import { PolyHavenAsset, AssetType } from "@/lib/services/polyhavenService";

// Asset Browser component interfaces
export interface AssetPanelProps {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
}

export interface AssetPanelViewProps {
  assetBrowser: ReturnType<
    typeof import("@/hooks/useAssetBrowser").useAssetBrowser
  >;
  onShowDialog: () => void;
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
}

export interface AssetDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  initialType?: AssetType;
}

export interface AssetDialogViewProps {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  initialType?: AssetType;
}

// Asset Browser Filter interfaces
export interface AssetFiltersProps {
  selectedType: AssetType;
  onTypeChange: (type: AssetType) => void;
  selectedCategories: string[];
  onCategoriesChange: (categories: string[]) => void;
  searchQuery: string;
  onSearchChange: (query: string) => void;
  compact?: boolean;
}

export interface AssetSearchInputProps {
  value: string;
  onChange: (value: string) => void;
  onClear: () => void;
  placeholder?: string;
  className?: string;
  compact?: boolean;
}

export interface AssetTypeTabsProps {
  selectedType: AssetType;
  onTypeChange: (type: AssetType) => void;
  className?: string;
}

export interface CategoryFilterPopoverProps {
  selectedCategories: string[];
  onCategoriesChange: (categories: string[]) => void;
  assetType: AssetType;
  compact?: boolean;
  categories?: Record<string, number>;
  loading?: boolean;
}

export interface SelectedCategoriesDisplayProps {
  selectedCategories: string[];
  onCategoryRemove: (category: string) => void;
  onClearAll: () => void;
}

// Asset Browser Grid interfaces
export interface AssetCardProps {
  asset: PolyHavenAsset & { id: string };
  onSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  isSelected?: boolean;
  compact?: boolean;
}

export interface AssetGridProps {
  assets: Array<PolyHavenAsset & { id: string }>;
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  compact?: boolean;
  loading?: boolean;
  error?: string;
}
