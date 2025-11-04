import { toast } from "sonner";

import {
  AssetType,
  PolyHavenAsset,
  HDRIAsset,
  TextureAsset,
  ModelAsset,
  AssetTypesResponse,
  AssetsResponse,
  PaginatedAssetsResponse,
  CategoriesResponse,
  Author,
  FileInfo,
  FileWithIncludes,
  AssetFiles,
} from "@/lib/types/assetBrowser";

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
