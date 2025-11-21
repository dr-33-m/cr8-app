import { createServerFn } from "@tanstack/react-start";
import { CheckHealthSchema } from "../validations/polyhaven";
import type { AssetTypesResponse } from "@/lib/types/assetBrowser";

export const getAssetTypesFn = createServerFn({ method: "GET" })
  .inputValidator(CheckHealthSchema)
  .handler(async (): Promise<AssetTypesResponse> => {
    const baseUrl = process.env.API_URL || "http://localhost:8000";

    const response = await fetch(`${baseUrl}/api/v1/polyhaven/types`, {
      method: "GET",
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "Unknown error occurred",
      }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  });
