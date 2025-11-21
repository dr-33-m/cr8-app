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

// Hook interfaces
export interface UseAssetBrowserOptions {
  initialType?: AssetType;
  initialSearch?: string;
  initialLimit?: number;
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
  enabled?: boolean;
}

export interface CategoriesState {
  categories: CategoriesResponse;
  selectedCategories: string[];
  loading: boolean;
  error: string | undefined;
}

export interface CategoriesOptions {
  assetType?: AssetType;
  initialCategories?: string[];
  enabled?: boolean;
}

export interface AssetDataState {
  assets: Array<PolyHavenAsset & { id: string }>;
  totalCount: number;
  loading: boolean;
  error: string | undefined;
}

export interface AssetDataOptions {
  assetType?: AssetType;
  categories?: string[];
  page?: number;
  limit?: number;
  search?: string;
  enabled?: boolean;
}

export interface PaginationState {
  page: number;
  limit: number;
  totalPages: number;
  totalCount: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface PaginationOptions {
  initialPage?: number;
  initialLimit?: number;
}

export interface SearchState {
  query: string;
  debouncedQuery: string;
}

export interface SearchOptions {
  initialQuery?: string;
  debounceMs?: number;
}

export interface SelectionState {
  selectedAsset: (PolyHavenAsset & { id: string }) | null;
}

export interface SelectionOptions {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
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
  error?: string | null;
}

// PolyHaven service interfaces
export type AssetType = "hdris" | "textures" | "models";

// Base asset interface
export interface PolyHavenAsset {
  name: string;
  type: number; // 0 = hdris, 1 = textures, 2 = models
  date_published: number;
  download_count: number;
  files_hash: string;
  authors: Record<string, string>;
  donated?: boolean;
  categories: string[];
  tags: string[];
  max_resolution: [number, number];
  thumbnail_url: string;
}

// Specific asset types
export interface HDRIAsset extends PolyHavenAsset {
  whitebalance?: number;
  backplates?: boolean;
  evs_cap: number;
  coords?: [number, number];
  date_taken?: number;
}

export interface TextureAsset extends PolyHavenAsset {
  dimensions: [number, number];
}

export interface ModelAsset extends PolyHavenAsset {
  lods?: number[];
}

// Response types
export interface AssetTypesResponse {
  types: string[];
}

export interface AssetsResponse {
  [assetId: string]: PolyHavenAsset;
}

export interface PaginatedAssetsResponse {
  assets: AssetsResponse;
  pagination: {
    page: number;
    limit: number;
    total_count: number;
    total_pages: number;
    has_next: boolean;
    has_prev: boolean;
  };
}

export interface CategoriesResponse {
  [category: string]: number;
}

export interface Author {
  name: string;
  link?: string;
  email?: string;
  donate?: string;
}

// File structure types
export interface FileInfo {
  url: string;
  md5: string;
  size: number;
}

export interface FileWithIncludes extends FileInfo {
  include?: Record<string, FileInfo>;
}

export interface AssetFiles {
  [key: string]: any; // Dynamic structure based on asset type
}
