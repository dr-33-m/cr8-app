import { createServerFn } from "@tanstack/react-start";
import { GetAssetFilesSchema } from "../validations/polyhaven";
import type { AssetFiles } from "@/lib/types/assetBrowser";

export const getAssetFilesFn = createServerFn({ method: "GET" })
  .inputValidator(GetAssetFilesSchema)
  .handler(async ({ data }): Promise<AssetFiles> => {
    const baseUrl = process.env.API_URL || "http://localhost:8000";

    const response = await fetch(
      `${baseUrl}/api/v1/polyhaven/assets/${data.assetId}/files`,
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
