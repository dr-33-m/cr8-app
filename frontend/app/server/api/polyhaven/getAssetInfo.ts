import { createServerFn } from "@tanstack/react-start";
import { GetAssetInfoSchema } from "../validations/polyhaven";
import type {
  HDRIAsset,
  TextureAsset,
  ModelAsset,
} from "@/lib/types/assetBrowser";

export const getAssetInfoFn = createServerFn({ method: "GET" })
  .inputValidator(GetAssetInfoSchema)
  .handler(async ({ data }): Promise<HDRIAsset | TextureAsset | ModelAsset> => {
    const baseUrl = process.env.API_URL || "http://localhost:8000";

    const response = await fetch(
      `${baseUrl}/api/v1/polyhaven/assets/${data.assetId}/info`,
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
