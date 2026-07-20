import { useCallback, useEffect, useRef, useState } from "react";
import { Loader2, Trash2, Upload } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  BlendFile,
  deleteBlendFileFn,
  listBlendFilesFn,
} from "@/server/api/storage/functions";
import { MAX_BLEND_BYTES, useBlendUpload } from "@/hooks/useBlendUpload";

interface BlendFileBrowserProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accessToken: string;
  onSelect: (file: BlendFile) => void;
}

function formatSize(bytes: number): string {
  if (bytes >= 1024 ** 3) return `${(bytes / 1024 ** 3).toFixed(1)} GB`;
  if (bytes >= 1024 ** 2) return `${Math.round(bytes / 1024 ** 2)} MB`;
  return `${Math.round(bytes / 1024)} KB`;
}

export function BlendFileBrowser({
  open,
  onOpenChange,
  accessToken,
  onSelect,
}: BlendFileBrowserProps) {
  const [files, setFiles] = useState<BlendFile[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [listError, setListError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    setIsLoading(true);
    setListError(null);
    try {
      setFiles(await listBlendFilesFn({ data: { accessToken } }));
    } catch (e) {
      setListError(e instanceof Error ? e.message : "Could not load your files");
    } finally {
      setIsLoading(false);
    }
  }, [accessToken]);

  const { addFiles, progress, error: uploadError, isUploading } =
    useBlendUpload(refresh);

  useEffect(() => {
    if (open) refresh();
  }, [open, refresh]);

  const handleDelete = async (key: string) => {
    setDeleting(key);
    try {
      await deleteBlendFileFn({ data: { accessToken, key } });
      await refresh();
    } finally {
      setDeleting(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    addFiles(Array.from(e.dataTransfer.files));
  };

  const error = uploadError ?? listError;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl! h-[80vh]! flex flex-col overflow-hidden">
        <DialogHeader className="shrink-0">
          <DialogTitle>Open Existing Project</DialogTitle>
          <DialogDescription>
            Your blend files, stored in the cloud. Up to{" "}
            {MAX_BLEND_BYTES / 1024 ** 3}GB each.
          </DialogDescription>
        </DialogHeader>

        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`shrink-0 rounded-lg border-2 border-dashed p-6 text-center cursor-pointer transition-colors ${
            isDragging ? "border-primary bg-primary/5" : "border-muted"
          }`}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".blend"
            multiple
            className="hidden"
            onChange={(e) => {
              addFiles(Array.from(e.target.files ?? []));
              e.target.value = "";
            }}
          />
          <Upload className="h-6 w-6 mx-auto mb-2 text-muted-foreground" />
          <p className="text-sm text-muted-foreground">
            Drop .blend files here, or click to browse
          </p>
        </div>

        {progress && (
          <div className="shrink-0 space-y-1">
            <div className="flex justify-between text-xs text-muted-foreground">
              <span className="truncate">{progress.filename}</span>
              <span>{progress.percent}%</span>
            </div>
            <div className="h-1.5 w-full rounded-full bg-muted overflow-hidden">
              <div
                className="h-full bg-primary transition-all"
                style={{ width: `${progress.percent}%` }}
              />
            </div>
          </div>
        )}

        {error && (
          <p className="shrink-0 text-sm text-destructive">{error}</p>
        )}

        <div className="flex-1 min-h-0 overflow-y-auto space-y-2 pr-1">
          {isLoading && files.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : files.length === 0 ? (
            <div className="flex items-center justify-center h-full text-sm text-muted-foreground">
              No blend files yet — upload one to get started.
            </div>
          ) : (
            files.map((file) => (
              <Card
                key={file.key}
                className="p-3 flex items-center gap-3 cursor-pointer hover:bg-accent transition-colors"
                onClick={() => onSelect(file)}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium truncate">{file.filename}</p>
                  <p className="text-xs text-muted-foreground">
                    {formatSize(file.size)} ·{" "}
                    {new Date(file.last_modified).toLocaleDateString()}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  disabled={deleting === file.key || isUploading}
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDelete(file.key);
                  }}
                >
                  {deleting === file.key ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </Button>
              </Card>
            ))
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
