import { createServerFn } from "@tanstack/react-start";

const engineUrl = process.env.API_URL || "http://localhost:8000";

/**
 * Proxy the engine health check through the server to avoid
 * cross-origin issues (studio.cr8-xyz.art → engine.cr8-xyz.art).
 */
export const checkEngineHealthFn = createServerFn({ method: "GET" }).handler(
  async () => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      const response = await fetch(`${engineUrl}/health`, {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return { healthy: response.ok };
    } catch {
      return { healthy: false };
    }
  }
);
