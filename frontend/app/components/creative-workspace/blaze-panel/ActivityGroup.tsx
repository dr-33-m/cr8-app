import { useState } from "react";
import { ChevronDown, ChevronRight, Check, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";
import { ChatEntry } from "@/lib/types/stores";

interface ActivityGroupProps {
  /** A run of consecutive activity entries, oldest first. */
  entries: ChatEntry[];
  /** True when this is the newest group and B.L.A.Z.E is still working. */
  isLive: boolean;
}

/**
 * A run of B.L.A.Z.E's tool steps, collapsed to a single line.
 *
 * A tool-heavy request emits a lot of these and they would otherwise push the
 * actual conversation off the panel. Collapsed shows only what is happening
 * right now (or, once finished, a count); expanding reveals the whole run.
 */
export function ActivityGroup({ entries, isLive }: ActivityGroupProps) {
  const [expanded, setExpanded] = useState(false);

  if (entries.length === 0) return null;

  const current = entries[entries.length - 1];
  const canExpand = entries.length > 1;

  return (
    <div className="pl-1">
      <button
        type="button"
        disabled={!canExpand}
        onClick={() => setExpanded((v) => !v)}
        className={cn(
          "flex w-full items-center gap-2 rounded-sm py-0.5 text-left text-xs text-muted-foreground transition-colors",
          canExpand && "hover:text-foreground"
        )}
      >
        {isLive ? (
          <Loader2 className="h-3 w-3 shrink-0 animate-spin text-primary" />
        ) : (
          <Check className="h-3 w-3 shrink-0 opacity-60" />
        )}

        <span className="truncate">
          {/* Live: the step actually running. Finished: a quiet summary. */}
          {isLive ? current.text : `${entries.length} step${entries.length !== 1 ? "s" : ""}`}
        </span>

        {canExpand && (
          <span className="ml-auto flex shrink-0 items-center gap-1 opacity-60">
            {isLive && `${entries.length}`}
            {expanded ? (
              <ChevronDown className="h-3 w-3" />
            ) : (
              <ChevronRight className="h-3 w-3" />
            )}
          </span>
        )}
      </button>

      {expanded && (
        <div className="mt-0.5 space-y-0.5 border-l border-border/60 pl-3">
          {entries.map((entry, i) => {
            const isCurrent = isLive && i === entries.length - 1;
            return (
              <div
                key={entry.id}
                className="flex items-center gap-2 text-xs text-muted-foreground"
              >
                {isCurrent ? (
                  <Loader2 className="h-2.5 w-2.5 shrink-0 animate-spin text-primary" />
                ) : (
                  <span className="h-1 w-1 shrink-0 rounded-full bg-muted-foreground/60" />
                )}
                <span className="truncate">{entry.text}</span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
