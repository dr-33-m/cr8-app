import { createServerFn } from "@tanstack/react-start";

const engineUrl = process.env.API_URL || "http://localhost:8000";

export interface BlendFile {
  key: string;
  filename: string;
  size: number;
  last_modified: string;
}

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

export const listBlendFilesFn = createServerFn({ method: "GET" })
  .inputValidator((data: { accessToken: string }) => data)
  .handler(async ({ data }): Promise<BlendFile[]> => {
    return engineFetch("/api/v1/storage/blend-files", data.accessToken);
  });

export const deleteBlendFileFn = createServerFn({ method: "POST" })
  .inputValidator((data: { accessToken: string; key: string }) => data)
  .handler(async ({ data }) => {
    await engineFetch(
      `/api/v1/storage/blend-files?key=${encodeURIComponent(data.key)}`,
      data.accessToken,
      { method: "DELETE" }
    );
    return { ok: true };
  });

/**
 * The four functions below back Uppy's @uppy/aws-s3 callbacks. They only ever
 * broker presigned URLs — the file bytes go from the browser straight to RustFS
 * and never pass through this server.
 */

export const getUploadParametersFn = createServerFn({ method: "POST" })
  .inputValidator(
    (data: { accessToken: string; filename: string; size: number }) => data
  )
  .handler(async ({ data }): Promise<{ upload_url: string; key: string }> => {
    return engineFetch("/api/v1/storage/blend-files/upload-url", data.accessToken, {
      method: "POST",
      body: JSON.stringify({ filename: data.filename, size: data.size }),
    });
  });

export const createMultipartUploadFn = createServerFn({ method: "POST" })
  .inputValidator((data: { accessToken: string; filename: string }) => data)
  .handler(async ({ data }): Promise<{ uploadId: string; key: string }> => {
    return engineFetch("/api/v1/storage/multipart/create", data.accessToken, {
      method: "POST",
      body: JSON.stringify({ filename: data.filename }),
    });
  });

export const signPartFn = createServerFn({ method: "POST" })
  .inputValidator(
    (data: {
      accessToken: string;
      key: string;
      uploadId: string;
      partNumber: number;
    }) => data
  )
  .handler(async ({ data }): Promise<{ url: string }> => {
    const query = new URLSearchParams({
      key: data.key,
      uploadId: data.uploadId,
      partNumber: String(data.partNumber),
    });
    return engineFetch(
      `/api/v1/storage/multipart/sign-part?${query}`,
      data.accessToken
    );
  });

export const listPartsFn = createServerFn({ method: "POST" })
  .inputValidator(
    (data: { accessToken: string; key: string; uploadId: string }) => data
  )
  .handler(
    async ({
      data,
    }): Promise<{ PartNumber: number; Size: number; ETag: string }[]> => {
      const query = new URLSearchParams({
        key: data.key,
        uploadId: data.uploadId,
      });
      return engineFetch(
        `/api/v1/storage/multipart/list-parts?${query}`,
        data.accessToken
      );
    }
  );

export const completeMultipartUploadFn = createServerFn({ method: "POST" })
  .inputValidator(
    (data: {
      accessToken: string;
      key: string;
      uploadId: string;
      parts: { PartNumber: number; ETag: string }[];
    }) => data
  )
  .handler(async ({ data }): Promise<{ location: string }> => {
    return engineFetch("/api/v1/storage/multipart/complete", data.accessToken, {
      method: "POST",
      body: JSON.stringify({
        key: data.key,
        uploadId: data.uploadId,
        parts: data.parts,
      }),
    });
  });

export const abortMultipartUploadFn = createServerFn({ method: "POST" })
  .inputValidator(
    (data: { accessToken: string; key: string; uploadId: string }) => data
  )
  .handler(async ({ data }) => {
    await engineFetch("/api/v1/storage/multipart/abort", data.accessToken, {
      method: "POST",
      body: JSON.stringify({ key: data.key, uploadId: data.uploadId }),
    });
    return { ok: true };
  });
