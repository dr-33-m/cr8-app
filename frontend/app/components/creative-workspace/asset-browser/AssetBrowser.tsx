import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import useBlazeChatStore from "@/store/blazeChatStore";
import { BlazeLogo } from "@/components/icons/BlazeLogo";
import { cn } from "@/lib/utils";
import { AssetPanel } from "./panels";
import { BlazeChatPanel } from "../blaze-panel/BlazeChatPanel";

/**
 * The right-hand card, carouselling between the asset browser and B.L.A.Z.E's
 * chat. B.L.A.Z.E's replies used to live in a modal dialog, which meant covering
 * the viewport to read what it had just done to the scene; here it shares the
 * space the asset browser already occupies.
 *
 * Both faces stay mounted and the track slides, so switching away and back keeps
 * the asset grid's scroll position and its in-flight search results.
 */
export function AssetBrowser() {
  const isVisible = useVisibilityStore((state) => state.isAssetSelectionVisible);
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleAssetSelection
  );
  const panel = useVisibilityStore((state) => state.rightPanel);
  const setRightPanel = useVisibilityStore((state) => state.setRightPanel);

  const isBusy = useBlazeChatStore((s) => s.isBusy);
  const hasUnseen = useBlazeChatStore((s) => s.hasUnseen);
  const markSeen = useBlazeChatStore((s) => s.markSeen);
  const entryCount = useBlazeChatStore((s) => s.entries.length);

  const showChat = panel === "chat";
  const chatOnScreen = isVisible && showChat;

  // While the chat is actually on screen there is nothing "unread" — you are
  // looking at it. Clearing as messages arrive stops the dot flashing on a
  // panel the user is already reading.
  useEffect(() => {
    if (chatOnScreen) markSeen();
  }, [chatOnScreen, entryCount, isBusy, markSeen]);

  const selectPanel = (next: "assets" | "chat") => {
    setRightPanel(next);
    if (next === "chat") markSeen();
  };

  return (
    <div
      className={`absolute right-4 top-1/2 transform -translate-y-1/2 transition-all duration-300
      ${isVisible ? "translate-x-0" : "translate-x-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -left-12 top-1/2 -translate-y-1/2"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronRight className="h-6 w-6" />
        ) : (
          <ChevronLeft className="h-6 w-6" />
        )}
      </Button>

      <Card className="flex h-[80vh] w-96 flex-col overflow-hidden">
        <CardHeader className="shrink-0 pb-3">
          <div className="flex items-center gap-1 rounded-lg bg-muted/20 p-1">
            <button
              type="button"
              onClick={() => selectPanel("assets")}
              className={cn(
                "flex-1 rounded-md px-3 py-1.5 text-sm transition-all duration-200",
                !showChat
                  ? "border border-primary/80 bg-primary/30 text-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Assets
            </button>
            <button
              type="button"
              onClick={() => selectPanel("chat")}
              className={cn(
                "relative flex flex-1 items-center justify-center gap-1.5 rounded-md px-3 py-1.5 text-sm transition-all duration-200",
                showChat
                  ? "border border-primary/80 bg-primary/30 text-foreground shadow-xs"
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              <BlazeLogo
                className={cn(
                  "h-3.5 w-3.5 transition-colors",
                  isBusy && "animate-pulse text-primary"
                )}
              />
              B.L.A.Z.E
              {!chatOnScreen && hasUnseen && !isBusy && (
                <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 rounded-full bg-primary" />
              )}
            </button>
          </div>
        </CardHeader>

        {/* Sliding track: both faces stay mounted so neither loses its state. */}
        <CardContent className="min-h-0 flex-1 overflow-hidden p-0">
          <div
            className="flex h-full w-[200%] transition-transform duration-300 ease-out"
            style={{ transform: showChat ? "translateX(-50%)" : "translateX(0)" }}
          >
            {/* pt-4 drops the Poly Haven header clear of the tab bar. The panel
                had spare room at the bottom, so this costs nothing. */}
            <div
              className="h-full w-1/2 overflow-y-auto px-6 pb-6 pt-4"
              aria-hidden={showChat}
            >
              <AssetPanel />
            </div>
            <div
              className="h-full w-1/2 overflow-hidden px-6 pb-6"
              aria-hidden={!showChat}
            >
              <BlazeChatPanel />
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
