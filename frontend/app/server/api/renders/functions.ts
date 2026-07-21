import { createServerFn } from "@tanstack/react-start";

const engineUrl = process.env.API_URL || "http://localhost:8000";

export interface RenderProject {
  project: string;
  image_count: number;
  video_count: number;
  cover_url: string | null;
  last_modified: string;
}

export interface RenderItem {
  key: string;
  filename: string;
  size: number;
  last_modified: string;
  url: string;
  /** Null when the best-effort thumbnail upload didn't land — fall back to `url`. */
  thumb_url: string | null;
}

export interface RenderMeta {
  size: number;
  last_modified: string | null;
  metadata: Record<string, string>;
}

export type RenderKind = "images" | "videos";

async function engineFetch(
  path: string,
  accessToken: string,
  init?: RequestInit
) {
  const response = await fetch(`${engineUrl}${path}`, {
    ...init,
    headers: {
      Authorization: `Bearer ${accessToken}`,
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    const detail = await response
      .json()
      .then((body) => body.detail)
      .catch(() => null);
    throw new Error(detail || `Request failed: ${response.status}`);
  }

  return response.status === 204 ? null : response.json();
}

export const listRenderProjectsFn = createServerFn({ method: "GET" })
  .inputValidator((data: { accessToken: string }) => data)
  .handler(async ({ data }): Promise<RenderProject[]> => {
    return engineFetch("/api/v1/renders/projects", data.accessToken);
  });

export const listRendersFn = createServerFn({ method: "GET" })
  .inputValidator(
    (data: { accessToken: string; project: string; kind: RenderKind }) => data
  )
  .handler(async ({ data }): Promise<RenderItem[]> => {
    const query = new URLSearchParams({
      project: data.project,
      kind: data.kind,
    });
    return engineFetch(`/api/v1/renders?${query}`, data.accessToken);
  });

export const getRenderMetaFn = createServerFn({ method: "GET" })
  .inputValidator((data: { accessToken: string; key: string }) => data)
  .handler(async ({ data }): Promise<RenderMeta> => {
    const query = new URLSearchParams({ key: data.key });
    return engineFetch(`/api/v1/renders/meta?${query}`, data.accessToken);
  });

export const deleteRenderFn = createServerFn({ method: "POST" })
  .inputValidator((data: { accessToken: string; key: string }) => data)
  .handler(async ({ data }) => {
    await engineFetch(
      `/api/v1/renders?key=${encodeURIComponent(data.key)}`,
      data.accessToken,
      { method: "DELETE" }
    );
    return { ok: true };
  });
