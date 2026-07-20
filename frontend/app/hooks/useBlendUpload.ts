import { useCallback, useEffect, useRef, useState } from "react";
import Uppy from "@uppy/core";
import AwsS3 from "@uppy/aws-s3";
import { getAccessTokenFn } from "@/server/auth/functions";
import {
  abortMultipartUploadFn,
  completeMultipartUploadFn,
  createMultipartUploadFn,
  getUploadParametersFn,
  listPartsFn,
  signPartFn,
} from "@/server/api/storage/functions";

/**
 * Single PUT below this, multipart above.
 *
 * Set deliberately rather than left to Uppy's default of 100 MiB (104_857_600):
 * RustFS sits behind a Cloudflare tunnel, which caps request bodies at 100 MB
 * (100_000_000). The default therefore overshoots the cap, and files in the
 * 100–104.8 MB band would take the single-PUT path and 413.
 *
 * Keep in sync with SINGLE_PUT_MAX_BYTES in backend storage_service.py.
 */
const SINGLE_PUT_MAX_BYTES = 50 * 1024 * 1024;

export const MAX_BLEND_BYTES = 2 * 1024 * 1024 * 1024;

export interface UploadProgress {
  filename: string;
  percent: number;
}

/**
 * Uppy types key/uploadId as optional on its multipart callbacks, but our
 * createMultipartUpload always returns both. Narrow once, loudly — a silent
 * `undefined` here would sign a part against the string "undefined".
 */
function requireUpload(key: string | undefined, uploadId: string | undefined) {
  if (!key || !uploadId) {
    throw new Error("Multipart upload is missing its key or uploadId");
  }
  return { key, uploadId };
}

/**
 * Uploads .blend files straight from the browser to RustFS via presigned URLs.
 * Bytes never pass through our servers — the server functions only broker URLs.
 *
 * Uppy touches `window`, so the instance is created in an effect rather than at
 * module scope: TanStack Start renders this on the server first.
 */
export function useBlendUpload(onComplete?: () => void) {
  const uppyRef = useRef<Uppy | null>(null);
  const [progress, setProgress] = useState<UploadProgress | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Held in a ref so the effect below can have an empty dependency list. If
  // onComplete were a dependency, a parent re-render that changed its identity
  // would destroy and rebuild Uppy — aborting an in-flight upload, which at 1GB
  // means losing a ten-minute transfer.
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  useEffect(() => {
    const token = async (): Promise<string> => {
      const { token } = await getAccessTokenFn();
      if (!token) throw new Error("Not signed in — cannot upload");
      return token;
    };

    const uppy = new Uppy({
      autoProceed: true,
      restrictions: {
        maxFileSize: MAX_BLEND_BYTES,
        allowedFileTypes: [".blend"],
      },
    }).use(AwsS3, {
      shouldUseMultipart: (file) => (file.size ?? 0) > SINGLE_PUT_MAX_BYTES,

      async getUploadParameters(file) {
        const { upload_url } = await getUploadParametersFn({
          data: {
            accessToken: await token(),
            filename: file.name ?? "untitled.blend",
            size: file.size ?? 0,
          },
        });
        // Content-Length is deliberately not set here: it's a forbidden header
        // name, so the browser strips it and sets the real value itself. The
        // backend still signs ContentLength, so an upload whose actual length
        // differs from the declared size fails the signature check.
        return { method: "PUT", url: upload_url };
      },

      async createMultipartUpload(file) {
        return createMultipartUploadFn({
          data: {
            accessToken: await token(),
            filename: file.name ?? "untitled.blend",
          },
        });
      },

      async signPart(file, { uploadId, key, partNumber }) {
        return signPartFn({
          data: {
            accessToken: await token(),
            key: requireUpload(key, uploadId).key,
            uploadId: requireUpload(key, uploadId).uploadId,
            partNumber,
          },
        });
      },

      // Required by Uppy for resume: on retry it asks which parts already landed
      // and skips them, so a blip at 900MB of a 1GB upload costs one part rather
      // than the whole transfer.
      async listParts(file, { uploadId, key }) {
        return listPartsFn({
          data: {
            accessToken: await token(),
            key: requireUpload(key, uploadId).key,
            uploadId: requireUpload(key, uploadId).uploadId,
          },
        });
      },

      async completeMultipartUpload(file, { uploadId, key, parts }) {
        return completeMultipartUploadFn({
          data: {
            accessToken: await token(),
            key: requireUpload(key, uploadId).key,
            uploadId: requireUpload(key, uploadId).uploadId,
            parts: parts.map((p) => ({
              PartNumber: p.PartNumber!,
              ETag: p.ETag!,
            })),
          },
        });
      },

      async abortMultipartUpload(file, { uploadId, key }) {
        await abortMultipartUploadFn({
          data: {
            accessToken: await token(),
            key: requireUpload(key, uploadId).key,
            uploadId: requireUpload(key, uploadId).uploadId,
          },
        });
      },
    });

    uppy.on("upload-progress", (file, p) => {
      if (!file || !p.bytesTotal) return;
      setProgress({
        filename: file.name ?? "",
        percent: Math.round((p.bytesUploaded / p.bytesTotal) * 100),
      });
    });

    uppy.on("upload-error", (_file, err) => {
      setError(err?.message ?? "Upload failed");
      setProgress(null);
    });

    uppy.on("restriction-failed", (_file, err) => {
      setError(err?.message ?? "File rejected");
    });

    uppy.on("complete", (result) => {
      setProgress(null);
      if (result.failed?.length) {
        setError(result.failed[0].error ?? "Upload failed");
        return;
      }
      uppy.clear();
      onCompleteRef.current?.();
    });

    uppyRef.current = uppy;

    return () => {
      // Aborts in-flight parts, so closing the dialog mid-upload doesn't strand
      // an incomplete multipart upload billing storage on the bucket.
      uppy.destroy();
      uppyRef.current = null;
    };
  }, []);

  const addFiles = useCallback((files: File[]) => {
    setError(null);
    for (const file of files) {
      try {
        uppyRef.current?.addFile({
          name: file.name,
          type: file.type,
          data: file,
        });
      } catch (e) {
        setError(e instanceof Error ? e.message : "Could not add file");
      }
    }
  }, []);

  return { addFiles, progress, error, isUploading: progress !== null };
}
