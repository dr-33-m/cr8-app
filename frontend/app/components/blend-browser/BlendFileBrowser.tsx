import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  FileImage,
  LayoutGrid,
  List as ListIcon,
  Loader2,
  MoreVertical,
  Plus,
  Search,
  Trash2,
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  BlendFile,
  deleteBlendFileFn,
  listBlendFilesFn,
} from "@/server/api/storage/functions";
import { MAX_BLEND_BYTES, useBlendUpload } from "@/hooks/useBlendUpload";
import { formatDate, formatSize } from "@/lib/formatters";

interface BlendFileBrowserProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  accessToken: string;
  onSelect: (file: BlendFile) => void;
}

type ViewMode = "grid" | "list";
type SortKey = "latest" | "oldest" | "name" | "size";

function sortFiles(files: BlendFile[], sort: SortKey): BlendFile[] {
  const copy = [...files];
  switch (sort) {
    case "oldest":
      return copy.sort(
        (a, b) =>
          new Date(a.last_modified).getTime() -
          new Date(b.last_modified).getTime()
      );
    case "name":
      return copy.sort((a, b) => a.filename.localeCompare(b.filename));
    case "size":
      return copy.sort((a, b) => b.size - a.size);
    case "latest":
    default:
      return copy.sort(
        (a, b) =>
          new Date(b.last_modified).getTime() -
          new Date(a.last_modified).getTime()
      );
  }
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
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>("latest");
  const [view, setView] = useState<ViewMode>("grid");
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

  const { addFiles, progress, error: uploadError } = useBlendUpload(refresh);

  useEffect(() => {
    if (open) refresh();
  }, [open, refresh]);

  const visibleFiles = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? files.filter((f) => f.filename.toLowerCase().includes(q))
      : files;
    return sortFiles(filtered, sort);
  }, [files, query, sort]);

  const handleDelete = async (key: string) => {
    if (deleting) return;
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

  const openFilePicker = () => inputRef.current?.click();

  const error = uploadError ?? listError;

  const FileMenu = ({ file }: { file: BlendFile }) => (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-7 w-7 shrink-0"
          disabled={deleting === file.key}
          onClick={(e) => e.stopPropagation()}
        >
          {deleting === file.key ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <MoreVertical className="h-4 w-4" />
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" onClick={(e) => e.stopPropagation()}>
        <DropdownMenuItem
          className="text-destructive focus:text-destructive"
          onClick={(e) => {
            e.stopPropagation();
            handleDelete(file.key);
          }}
        >
          <Trash2 className="h-4 w-4" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-5xl! h-[80vh]! flex flex-col overflow-hidden gap-4">
        <DialogHeader className="shrink-0">
          <DialogTitle className="text-2xl font-semibold">
            Open Existing Project
          </DialogTitle>
          <DialogDescription>
            Your files, stored in the cloud. Up to{" "}
            {MAX_BLEND_BYTES / 1024 ** 3}GB each.
          </DialogDescription>
        </DialogHeader>

        {/* Toolbar: search · sort · view toggle */}
        <div className="shrink-0 flex flex-wrap items-center gap-3">
          <div className="relative flex-1 min-w-[200px]">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search projects..."
              className="pl-9"
            />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">
              Sort by
            </span>
            <Select value={sort} onValueChange={(v) => setSort(v as SortKey)}>
              <SelectTrigger className="w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="latest">Latest</SelectItem>
                <SelectItem value="oldest">Oldest</SelectItem>
                <SelectItem value="name">Name A–Z</SelectItem>
                <SelectItem value="size">Size</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="flex items-center gap-0.5 rounded-md border p-0.5">
            <button
              type="button"
              aria-label="Grid view"
              onClick={() => setView("grid")}
              className={`flex h-7 w-7 items-center justify-center rounded transition-colors ${
                view === "grid"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <LayoutGrid className="h-4 w-4" />
            </button>
            <button
              type="button"
              aria-label="List view"
              onClick={() => setView("list")}
              className={`flex h-7 w-7 items-center justify-center rounded transition-colors ${
                view === "list"
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:text-foreground"
              }`}
            >
              <ListIcon className="h-4 w-4" />
            </button>
          </div>
        </div>

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

        {error && <p className="shrink-0 text-sm text-destructive">{error}</p>}

        {/* Content — whole area is a drop target */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setIsDragging(true);
          }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
          className={`flex-1 min-h-0 overflow-y-auto rounded-lg pr-1 transition-colors ${
            isDragging ? "ring-2 ring-primary ring-inset bg-primary/5" : ""
          }`}
        >
          {isLoading && files.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              <Loader2 className="h-5 w-5 animate-spin" />
            </div>
          ) : view === "grid" ? (
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 p-0.5">
              {visibleFiles.map((file) => (
                <Card
                  key={file.key}
                  className="relative p-4 flex flex-col items-center justify-center gap-2 min-h-[180px] cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => onSelect(file)}
                >
                  <div className="absolute top-2 right-2">
                    <FileMenu file={file} />
                  </div>
                  <FileImage className="h-14 w-14 text-primary" strokeWidth={1} />
                  <p className="font-medium truncate max-w-full text-center px-2">
                    {file.filename}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatSize(file.size)}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatDate(file.last_modified)}
                  </p>
                </Card>
              ))}

              {/* Add Files tile */}
              <button
                type="button"
                onClick={openFilePicker}
                className="rounded-xl border-2 border-dashed border-muted flex flex-col items-center justify-center gap-2 min-h-[180px] p-4 cursor-pointer hover:border-primary/50 transition-colors"
              >
                <div className="h-12 w-12 rounded-md border flex items-center justify-center">
                  <Plus className="h-6 w-6" />
                </div>
                <p className="font-medium">Add Files</p>
                <p className="text-xs text-muted-foreground text-center">
                  <span className="text-primary">Browse</span> or drop .blend
                  files here
                </p>
              </button>
            </div>
          ) : (
            <div className="space-y-2 p-0.5">
              {visibleFiles.map((file) => (
                <Card
                  key={file.key}
                  className="p-3 flex items-center gap-3 cursor-pointer hover:bg-accent transition-colors"
                  onClick={() => onSelect(file)}
                >
                  <FileImage className="h-8 w-8 text-primary shrink-0" strokeWidth={1} />
                  <div className="flex-1 min-w-0">
                    <p className="font-medium truncate">{file.filename}</p>
                    <p className="text-xs text-muted-foreground">
                      {formatSize(file.size)} · {formatDate(file.last_modified)}
                    </p>
                  </div>
                  <FileMenu file={file} />
                </Card>
              ))}

              <button
                type="button"
                onClick={openFilePicker}
                className="w-full rounded-lg border-2 border-dashed border-muted flex items-center justify-center gap-2 p-4 text-sm cursor-pointer hover:border-primary/50 transition-colors"
              >
                <Plus className="h-4 w-4" />
                <span>
                  <span className="text-primary">Browse</span> or drop .blend
                  files here
                </span>
              </button>
            </div>
          )}

          {!isLoading && !error && files.length > 0 && visibleFiles.length === 0 && (
            <p className="text-center text-sm text-muted-foreground py-6">
              No projects match “{query}”.
            </p>
          )}
          {!isLoading && !error && files.length === 0 && (
            <p className="text-center text-sm text-muted-foreground pt-4">
              No blend files yet — add one to get started.
            </p>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
