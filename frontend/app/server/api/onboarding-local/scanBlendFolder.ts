import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import type { ScanBlendFolderResponse } from "@/lib/types/onboarding";

const ScanFolderSchema = z.object({
  folderPath: z.string().min(1),
});

export const scanBlendFolder = createServerFn({ method: "GET" })
  .inputValidator(ScanFolderSchema)
  .handler(async ({ data }): Promise<ScanBlendFolderResponse> => {
    const baseUrl = process.env.API_URL || "http://localhost:8000";
    const queryParams = new URLSearchParams({
      folder_path: data.folderPath,
    });

    const response = await fetch(
      `${baseUrl}/api/v1/scan-blend-folder?${queryParams.toString()}`,
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
