import { toast } from "sonner";

// Asset type definitions
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

class PolyHavenService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  }

  async getAssetTypes(): Promise<string[]> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/polyhaven/types`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: AssetTypesResponse = await response.json();
      return data.types;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch asset types";
      toast.error(`Error loading asset types: ${errorMessage}`);
      throw error;
    }
  }

  async getAssets(
    assetType?: AssetType,
    categories?: string[]
  ): Promise<PaginatedAssetsResponse> {
    try {
      const params = new URLSearchParams();

      if (assetType) {
        params.append("type", assetType);
      }

      if (categories && categories.length > 0) {
        params.append("categories", categories.join(","));
      }

      // Use default pagination (page 1, limit 20)
      params.append("page", "1");
      params.append("limit", "20");

      const url = `${this.baseUrl}/api/v1/polyhaven/assets?${params.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: PaginatedAssetsResponse = await response.json();
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch assets";
      toast.error(`Error loading assets: ${errorMessage}`);
      throw error;
    }
  }

  async getAssetsPaginated(
    options: {
      assetType?: AssetType;
      categories?: string[];
      page?: number;
      limit?: number;
      search?: string;
    } = {}
  ): Promise<PaginatedAssetsResponse> {
    try {
      const { assetType, categories, page = 1, limit = 20, search } = options;

      const params = new URLSearchParams();

      if (assetType) {
        params.append("type", assetType);
      }

      if (categories && categories.length > 0) {
        params.append("categories", categories.join(","));
      }

      params.append("page", page.toString());
      params.append("limit", limit.toString());

      if (search) {
        params.append("search", search);
      }

      const url = `${this.baseUrl}/api/v1/polyhaven/assets?${params.toString()}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: PaginatedAssetsResponse = await response.json();
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error
          ? error.message
          : "Failed to fetch paginated assets";
      toast.error(`Error loading assets: ${errorMessage}`);
      throw error;
    }
  }

  async getAssetInfo(
    assetId: string
  ): Promise<HDRIAsset | TextureAsset | ModelAsset> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/v1/polyhaven/assets/${assetId}/info`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch asset info";
      toast.error(`Error loading asset info: ${errorMessage}`);
      throw error;
    }
  }

  async getAssetFiles(assetId: string): Promise<AssetFiles> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/v1/polyhaven/assets/${assetId}/files`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: AssetFiles = await response.json();
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch asset files";
      toast.error(`Error loading asset files: ${errorMessage}`);
      throw error;
    }
  }

  async getCategories(
    assetType: AssetType,
    inCategories?: string[]
  ): Promise<CategoriesResponse> {
    try {
      const params = new URLSearchParams();

      if (inCategories && inCategories.length > 0) {
        params.append("in", inCategories.join(","));
      }

      const url = `${this.baseUrl}/api/v1/polyhaven/categories/${assetType}${params.toString() ? `?${params.toString()}` : ""}`;
      const response = await fetch(url);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: CategoriesResponse = await response.json();
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch categories";
      toast.error(`Error loading categories: ${errorMessage}`);
      throw error;
    }
  }

  async getAuthorInfo(authorId: string): Promise<Author> {
    try {
      const response = await fetch(
        `${this.baseUrl}/api/v1/polyhaven/authors/${encodeURIComponent(authorId)}`
      );

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data: Author = await response.json();
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to fetch author info";
      toast.error(`Error loading author info: ${errorMessage}`);
      throw error;
    }
  }

  async checkHealth(): Promise<{
    status: string;
    message: string;
    available_types?: string[];
  }> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/polyhaven/health`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to check health";
      toast.error(`Poly Haven service health check failed: ${errorMessage}`);
      throw error;
    }
  }

  // Utility functions
  getAssetTypeFromNumber(type: number): AssetType {
    switch (type) {
      case 0:
        return "hdris";
      case 1:
        return "textures";
      case 2:
        return "models";
      default:
        return "textures";
    }
  }

  getAssetTypeDisplayName(type: AssetType): string {
    switch (type) {
      case "hdris":
        return "HDRIs";
      case "textures":
        return "Textures";
      case "models":
        return "Models";
      default:
        return "Assets";
    }
  }

  // Convert assets response to array format for easier handling
  convertAssetsToArray(
    assetsResponse: AssetsResponse
  ): Array<PolyHavenAsset & { id: string }> {
    return Object.entries(assetsResponse).map(([id, asset]) => ({
      ...asset,
      id,
    }));
  }
}

export const polyhavenService = new PolyHavenService();
