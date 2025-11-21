import { createServerFn } from "@tanstack/react-start";
import { GetCategoriesSchema } from "../validations/polyhaven";
import type { CategoriesResponse } from "@/lib/types/assetBrowser";

export const getCategoriesFn = createServerFn({ method: "GET" })
  .inputValidator(GetCategoriesSchema)
  .handler(async ({ data }): Promise<CategoriesResponse> => {
    const baseUrl = process.env.API_URL || "http://localhost:8000";

    const params = new URLSearchParams();

    if (data.inCategories && data.inCategories.length > 0) {
      params.append("in", data.inCategories.join(","));
    }

    const url = `${baseUrl}/api/v1/polyhaven/categories/${data.assetType}${
      params.toString() ? `?${params.toString()}` : ""
    }`;

    const response = await fetch(url, {
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
