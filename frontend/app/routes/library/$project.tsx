import { useCallback, useEffect, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { ArrowLeft, Download, Film, Images, Loader2, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  deleteRenderFn,
  getRenderMetaFn,
  listRendersFn,
  type RenderItem,
  type RenderKind,
  type RenderMeta,
} from "@/server/api/renders/functions";
import { formatDate, formatSize } from "@/lib/formatters";

export const Route = createFileRoute("/library/$project")({
  component: ProjectLibrary,
});

function ProjectLibrary() {
  const { auth } = Route.useRouteContext();
  const { project } = Route.useParams();
  const accessToken = auth.isAuthenticated ? auth.accessToken! : "";

  const [kind, setKind] = useState<RenderKind>("images");
  const [items, setItems] = useState<RenderItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<RenderItem | null>(null);
  const [meta, setMeta] = useState<RenderMeta | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setItems(await listRendersFn({ data: { accessToken, project, kind } }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load renders");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken, project, kind]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  // Settings are one HEAD per render, fetched only when a preview opens —
  // keeping them out of the listing is what makes the grid a single request.
  const openPreview = useCallback(
    async (item: RenderItem) => {
      setSelected(item);
      setMeta(null);
      try {
        setMeta(await getRenderMetaFn({ data: { accessToken, key: item.key } }));
      } catch {
        // Details are a nice-to-have; the image itself is already on screen.
      }
    },
    [accessToken]
  );

  const handleDelete = useCallback(
    async (item: RenderItem) => {
      setDeleting(item.key);
      try {
        await deleteRenderFn({ data: { accessToken, key: item.key } });
        setSelected(null);
        toast.success("Render deleted");
        await refresh();
      } catch (e) {
        toast.error(e instanceof Error ? e.message : "Could not delete render");
      } finally {
        setDeleting(null);
      }
    },
    [accessToken, refresh]
  );

  return (
    <div className="min-h-screen px-4 pt-28 pb-12">
      <div className="container mx-auto">
        <Link
          to="/library"
          className="mb-4 inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="h-4 w-4" />
          Library
        </Link>

        <h1 className="mb-4 text-2xl font-semibold">{project}</h1>

        <div className="mb-6 flex gap-2">
          <Button
            variant={kind === "images" ? "default" : "outline"}
            size="sm"
            onClick={() => setKind("images")}
          >
            <Images className="mr-1.5 h-4 w-4" />
            Images
          </Button>
          <Button
            variant={kind === "videos" ? "default" : "outline"}
            size="sm"
            onClick={() => setKind("videos")}
          >
            <Film className="mr-1.5 h-4 w-4" />
            Videos
          </Button>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <p className="py-24 text-center text-sm text-destructive">{error}</p>
        ) : items.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-24 text-center">
            {kind === "videos" ? (
              <>
                <Film className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm font-medium">No videos yet</p>
                <p className="text-sm text-muted-foreground">
                  Animation rendering is coming soon.
                </p>
              </>
            ) : (
              <>
                <Images className="h-8 w-8 text-muted-foreground" />
                <p className="text-sm font-medium">No images in this project</p>
              </>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {items.map((item) => (
              <Card
                key={item.key}
                className="cursor-pointer overflow-hidden p-0 transition-colors hover:border-primary"
                onClick={() => openPreview(item)}
              >
                <div className="aspect-video w-full bg-muted">
                  <img
                    // thumb_url is null when the best-effort thumbnail upload
                    // didn't land — the full image is a heavier but correct
                    // fallback, and better than a broken preview.
                    src={item.thumb_url ?? item.url}
                    alt={item.filename}
                    loading="lazy"
                    className="h-full w-full object-cover"
                  />
                </div>
                <div className="space-y-0.5 p-3">
                  <p className="truncate text-sm font-medium">{item.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatSize(item.size)} · {formatDate(item.last_modified)}
                  </p>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      <Dialog
        open={!!selected}
        onOpenChange={(open) => !open && setSelected(null)}
      >
        <DialogContent className="sm:max-w-3xl">
          <DialogHeader>
            <DialogTitle className="truncate pr-8">
              {selected?.filename}
            </DialogTitle>
          </DialogHeader>

          {selected && (
            <>
              <img
                src={selected.url}
                alt={selected.filename}
                className="max-h-[60vh] w-full rounded-md object-contain"
              />

              <div className="flex flex-wrap items-center justify-between gap-3">
                <div className="text-xs text-muted-foreground">
                  {formatSize(selected.size)} ·{" "}
                  {formatDate(selected.last_modified)}
                  {meta?.metadata?.engine && (
                    <>
                      {" "}
                      · {meta.metadata.engine}
                      {meta.metadata.resolution && ` ${meta.metadata.resolution.toUpperCase()}`}
                      {meta.metadata.camera && ` · ${meta.metadata.camera}`}
                    </>
                  )}
                </div>
                <div className="flex gap-2">
                  <Button variant="outline" size="sm" asChild>
                    {/* download_url, not url: the `download` attribute is
                        ignored cross-origin, so the save is forced by the
                        Content-Disposition the engine signs into this URL. */}
                    <a href={selected.download_url} download={selected.filename}>
                      <Download className="mr-1.5 h-4 w-4" />
                      Download
                    </a>
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    disabled={deleting === selected.key}
                    onClick={() => handleDelete(selected)}
                  >
                    {deleting === selected.key ? (
                      <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                    ) : (
                      <Trash2 className="mr-1.5 h-4 w-4" />
                    )}
                    Delete
                  </Button>
                </div>
              </div>
            </>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
