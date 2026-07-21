/**
 * Display formatters shared by the file browsers and the render library.
 *
 * Lifted out of BlendFileBrowser rather than copied, so the two galleries can't
 * drift into showing the same date two different ways.
 */

export function formatSize(bytes: number): string {
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes >= 1024 ** 2) return `${Math.round(bytes / 1024 ** 2)} MB`;
  return `${Math.round(bytes / 1024)} KB`;
}

// dd/mm/yyyy • h:mm AM/PM — matches the gallery mockup.
export function formatDate(iso: string): string {
  const d = new Date(iso);
  const date = d.toLocaleDateString("en-GB");
  const time = d.toLocaleTimeString("en-US", {
    hour: "numeric",
    minute: "2-digit",
  });
  return `${date} • ${time}`;
}

/** Seconds as m:ss — used by the render overlay's elapsed counter. */
export function formatElapsedSeconds(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = seconds % 60;
  return `${mins}:${secs.toString().padStart(2, "0")}`;
}
