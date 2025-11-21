import { createServerFn } from "@tanstack/react-start";
import { GetAuthorInfoSchema } from "../validations/polyhaven";
import type { Author } from "@/lib/types/assetBrowser";

export const getAuthorInfoFn = createServerFn({ method: "GET" })
  .inputValidator(GetAuthorInfoSchema)
  .handler(async ({ data }): Promise<Author> => {
    const baseUrl = process.env.API_URL || "http://localhost:8000";

    const response = await fetch(
      `${baseUrl}/api/v1/polyhaven/authors/${encodeURIComponent(
        data.authorId
      )}`,
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
