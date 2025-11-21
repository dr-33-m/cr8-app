import { createServerFn } from "@tanstack/react-start";
import { CheckHealthSchema } from "../validations/polyhaven";

export const checkHealthFn = createServerFn({ method: "GET" })
  .inputValidator(CheckHealthSchema)
  .handler(
    async (): Promise<{
      status: string;
      message: string;
      available_types?: string[];
    }> => {
      const baseUrl = process.env.API_URL || "http://localhost:8000";

      const response = await fetch(`${baseUrl}/api/v1/polyhaven/health`, {
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
    }
  );
