import { useCallback, useEffect, useState } from "react";
import { createFileRoute, Link } from "@tanstack/react-router";
import { Images, Loader2 } from "lucide-react";
import { Card } from "@/components/ui/card";
import {
  listRenderProjectsFn,
  type RenderProject,
} from "@/server/api/renders/functions";
import { formatDate } from "@/lib/formatters";

export const Route = createFileRoute("/library/")({
  component: LibraryIndex,
});

function countLabel(project: RenderProject): string {
  const parts: string[] = [];
  if (project.image_count) {
    parts.push(`${project.image_count} image${project.image_count === 1 ? "" : "s"}`);
  }
  if (project.video_count) {
    parts.push(`${project.video_count} video${project.video_count === 1 ? "" : "s"}`);
  }
  return parts.join(" · ") || "Empty";
}

function LibraryIndex() {
  const { auth } = Route.useRouteContext();
  const accessToken = auth.isAuthenticated ? auth.accessToken! : "";

  const [projects, setProjects] = useState<RenderProject[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setProjects(await listRenderProjectsFn({ data: { accessToken } }));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load your renders");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return (
    <div className="min-h-screen px-4 pt-28 pb-12">
      <div className="container mx-auto">
        <div className="mb-6">
          <h1 className="text-2xl font-semibold">Library</h1>
          <p className="text-sm text-muted-foreground">
            Renders from your projects
          </p>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-24">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : error ? (
          <p className="py-24 text-center text-sm text-destructive">{error}</p>
        ) : projects.length === 0 ? (
          <div className="flex flex-col items-center justify-center gap-2 py-24 text-center">
            <Images className="h-8 w-8 text-muted-foreground" />
            <p className="text-sm font-medium">No renders yet</p>
            <p className="text-sm text-muted-foreground">
              Render an image from the workspace and it will appear here.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4">
            {projects.map((project) => (
              <Link
                key={project.project}
                to="/library/$project"
                params={{ project: project.project }}
              >
                <Card className="overflow-hidden p-0 transition-colors hover:border-primary">
                  <div className="aspect-video w-full bg-muted">
                    {project.cover_url ? (
                      <img
                        src={project.cover_url}
                        alt={project.project}
                        loading="lazy"
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <div className="flex h-full w-full items-center justify-center">
                        <Images className="h-6 w-6 text-muted-foreground" />
                      </div>
                    )}
                  </div>
                  <div className="space-y-0.5 p-3">
                    <p className="truncate text-sm font-medium">
                      {project.project}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {countLabel(project)}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      {formatDate(project.last_modified)}
                    </p>
                  </div>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
