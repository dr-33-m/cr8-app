import { Inbox, Image } from "lucide-react";

// Custom suggestion renderer for inbox items
export const renderInboxSuggestion = (
  suggestion: any,
  search: string,
  highlightedDisplay: React.ReactNode,
  index: number,
  focused: boolean
) => {
  return (
    <div
      className={`px-3 py-2 flex items-center gap-3 rounded-md mx-1 ${
        focused ? "bg-accent text-accent-foreground" : "text-popover-foreground"
      }`}
    >
      <div className="shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-base bg-primary/20 border border-primary/30">
        <Inbox className="h-4 w-4 text-primary" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{highlightedDisplay}</div>
        <div className="text-xs text-muted-foreground truncate">
          {suggestion.type} • inbox
        </div>
      </div>
    </div>
  );
};

// Custom suggestion renderer for scene objects
export const renderSceneSuggestion = (
  suggestion: any,
  search: string,
  highlightedDisplay: React.ReactNode,
  index: number,
  focused: boolean
) => {
  return (
    <div
      className={`px-3 py-2 flex items-center gap-3 rounded-md mx-1 ${
        focused ? "bg-accent text-accent-foreground" : "text-popover-foreground"
      }`}
    >
      <div className="shrink-0 w-7 h-7 rounded-md flex items-center justify-center text-base bg-secondary/30 border border-secondary/50">
        <Image className="h-4 w-4 text-secondary-foreground" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium truncate">{highlightedDisplay}</div>
        <div className="text-xs text-muted-foreground truncate">
          {suggestion.type} • scene
        </div>
      </div>
    </div>
  );
};
