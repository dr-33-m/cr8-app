import { createServerFn } from "@tanstack/react-start";
import { GetAssetsSchema } from "../validations/polyhaven";
import type { PaginatedAssetsResponse } from "@/lib/types/assetBrowser";

export const getAssetsFn = createServerFn({ method: "GET" })
  .inputValidator(GetAssetsSchema)
  .handler(async ({ data }): Promise<PaginatedAssetsResponse> => {
    const baseUrl = process.env.API_URL || "http://localhost:8000";

    const params = new URLSearchParams();

    if (data.assetType) {
      params.append("type", data.assetType);
    }

    if (data.categories && data.categories.length > 0) {
      params.append("categories", data.categories.join(","));
    }

    params.append("page", "1");
    params.append("limit", "20");

    const response = await fetch(
      `${baseUrl}/api/v1/polyhaven/assets?${params.toString()}`,
      {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "Unknown error occurred",
      }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  });
