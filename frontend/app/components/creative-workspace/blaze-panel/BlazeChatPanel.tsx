import { useCallback, useEffect, useMemo, useRef } from "react";
import { Loader2, RotateCw } from "lucide-react";
import { EmptyState } from "@/components/placeholders/EmptyState";
import { BlazeLogo } from "@/components/icons/BlazeLogo";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import useBlazeChatStore from "@/store/blazeChatStore";
import { ChatEntry } from "@/lib/types/stores";
import { ActivityGroup } from "./ActivityGroup";
import { Markdown } from "./Markdown";

const formatTime = (at: number) =>
  new Date(at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

/** A message bubble. Activity lines are handled separately by ActivityGroup. */
function Message({
  entry,
  onRetry,
}: {
  entry: ChatEntry;
  /** Present only on the newest error when there is something to replay. */
  onRetry?: () => void;
}) {
  if (entry.kind === "user") {
    return (
      <div className="flex justify-end">
        {/* The user's own text is shown verbatim — they typed it, not markdown. */}
        <div className="max-w-[85%] whitespace-pre-wrap break-words rounded-lg rounded-br-sm bg-primary/20 px-3 py-2 text-sm">
          {entry.text}
          <span className="mt-1 block text-[10px] opacity-60">
            {formatTime(entry.at)}
          </span>
        </div>
      </div>
    );
  }

  const isError = entry.kind === "error";

  return (
    <div className="flex justify-start">
      <div
        className={cn(
          "max-w-[85%] break-words rounded-lg rounded-bl-sm border px-3 py-2",
          isError
            ? "border-destructive/40 bg-destructive/10 text-destructive"
            : "bg-secondary/20"
        )}
      >
        {isError ? (
          <div className="whitespace-pre-wrap text-sm">{entry.text}</div>
        ) : (
          <Markdown>{entry.text}</Markdown>
        )}

        {onRetry && (
          <Button
            variant="outline"
            size="sm"
            onClick={onRetry}
            className="mt-2 h-7 border-destructive/40 px-2 text-xs hover:bg-destructive/10"
          >
            <RotateCw className="mr-1.5 h-3 w-3" />
            Retry
          </Button>
        )}

        <span className="mt-1 block text-[10px] opacity-60">
          {formatTime(entry.at)}
        </span>
      </div>
    </div>
  );
}

/** A message, or a collapsed run of consecutive tool steps. */
type Block =
  | { type: "message"; entry: ChatEntry }
  | { type: "activity"; entries: ChatEntry[]; key: string };

export function BlazeChatPanel() {
  const entries = useBlazeChatStore((s) => s.entries);
  const isBusy = useBlazeChatStore((s) => s.isBusy);
  const lastRequest = useBlazeChatStore((s) => s.lastRequest);
  const { sendMessage, isFullyConnected } = useWebSocketContext();

  const scrollRef = useRef<HTMLDivElement | null>(null);

  // Replay the failed turn verbatim — same context and mentions, so B.L.A.Z.E
  // sees exactly what it saw before. Common after a transient upstream
  // "Provider returned error", where nothing about the request was wrong.
  const retry = useCallback(() => {
    if (!lastRequest || isBusy || !isFullyConnected) return;
    const chat = useBlazeChatStore.getState();
    chat.addActivity("retry", "Retrying…");
    chat.setBusy(true);
    sendMessage(lastRequest);
  }, [lastRequest, isBusy, isFullyConnected, sendMessage]);

  // Offer retry only on the newest entry, and only while it is still the
  // outcome of the last turn — a retry button under an old error you have
  // already moved past would replay the wrong thing.
  const canRetry = Boolean(lastRequest) && !isBusy && isFullyConnected;
  const lastEntry = entries[entries.length - 1];
  const retryableId =
    canRetry && lastEntry?.kind === "error" ? lastEntry.id : null;

  // Collapse consecutive activity entries into one block so a tool-heavy turn
  // doesn't push the conversation off the panel.
  const blocks = useMemo(() => {
    const out: Block[] = [];
    for (const entry of entries) {
      if (entry.kind === "activity") {
        const last = out[out.length - 1];
        if (last && last.type === "activity") {
          last.entries.push(entry);
          continue;
        }
        out.push({ type: "activity", entries: [entry], key: entry.id });
      } else {
        out.push({ type: "message", entry });
      }
    }
    return out;
  }, [entries]);

  // Always pin to the newest message. Driven off the entry count and the text of
  // the last entry, so a live activity line updating in place still scrolls.
  const lastText = entries[entries.length - 1]?.text ?? "";
  useEffect(() => {
    const el = scrollRef.current;
    if (!el) return;
    // Set scrollTop directly rather than scrollIntoView — this panel sits inside
    // an absolutely-positioned card, and scrollIntoView would scroll the page
    // behind it as well.
    el.scrollTop = el.scrollHeight;
  }, [entries.length, lastText, isBusy]);

  if (entries.length === 0) {
    return (
      <EmptyState
        title="No messages yet"
        description="Your conversation with B.L.A.Z.E will show up here"
        hint="💡 Ask B.L.A.Z.E to add or arrange something in your scene"
        icon={<BlazeLogo className="mx-auto h-12 w-12 text-secondary" />}
      />
    );
  }

  const lastBlockIndex = blocks.length - 1;

  return (
    <div className="flex h-full flex-col">
      <div
        ref={scrollRef}
        className="flex-1 space-y-2 overflow-y-auto pr-1"
        style={{ scrollBehavior: "smooth" }}
      >
        {blocks.map((block, i) =>
          block.type === "activity" ? (
            <ActivityGroup
              key={block.key}
              entries={block.entries}
              isLive={isBusy && i === lastBlockIndex}
            />
          ) : (
            <Message
              key={block.entry.id}
              entry={block.entry}
              onRetry={
                block.entry.id === retryableId ? retry : undefined
              }
            />
          )
        )}

        {/* B.L.A.Z.E is working but hasn't reported a step yet. */}
        {isBusy && blocks[lastBlockIndex]?.type !== "activity" && (
          <div className="flex items-center gap-2 pl-1 text-xs text-muted-foreground">
            <Loader2 className="h-3 w-3 animate-spin text-primary" />
            Working…
          </div>
        )}
      </div>
    </div>
  );
}
