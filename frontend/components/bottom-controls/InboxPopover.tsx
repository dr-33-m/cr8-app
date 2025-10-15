import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Inbox, X } from "lucide-react";
import { toast } from "sonner";
import useInboxStore from "@/store/inboxStore";

export function InboxPopover() {
  const [inboxPopoverOpen, setInboxPopoverOpen] = useState(false);
  const [inboxFilter, setInboxFilter] = useState<
    "hdris" | "textures" | "models"
  >("hdris");

  const inboxStore = useInboxStore();
  const inboxCount = inboxStore.getItemCount();

  return (
    <Popover open={inboxPopoverOpen} onOpenChange={setInboxPopoverOpen}>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="absolute left-3 bottom-1 h-6 w-6 text-white/60 hover:text-white hover:bg-white/10"
        >
          <Inbox className="h-4 w-4" />
          {inboxCount > 0 && (
            <Badge className="absolute -top-2 -right-2 h-4 min-w-[16px] px-1 text-[10px] bg-primary border-primary">
              {inboxCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-80 bg-cr8-charcoal/10 backdrop-blur-md border-white/10 text-white"
        side="top"
        align="end"
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="font-medium">Inbox</h4>
            {inboxCount > 0 && (
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  inboxStore.clearAll();
                  toast.info("Inbox cleared");
                }}
                className="text-xs text-white/60 hover:text-white"
              >
                Clear all
              </Button>
            )}
          </div>

          {/* Asset Type Tabs */}
          <Tabs
            value={inboxFilter}
            onValueChange={(value) =>
              setInboxFilter(value as "hdris" | "textures" | "models")
            }
          >
            <TabsList className="grid w-full grid-cols-3 bg-white/5 border border-white/10">
              <TabsTrigger
                value="hdris"
                className="data-[state=active]:bg-blue-500/20 data-[state=active]:text-blue-300 text-xs"
              >
                HDRIs
                <Badge className="ml-1 h-4 min-w-[16px] px-1 text-[10px] bg-blue-500/30 border-blue-500/50">
                  {
                    inboxStore.items.filter((item) => item.type === "hdris")
                      .length
                  }
                </Badge>
              </TabsTrigger>
              <TabsTrigger
                value="textures"
                className="data-[state=active]:bg-green-500/20 data-[state=active]:text-green-300 text-xs"
              >
                Textures
                <Badge className="ml-1 h-4 min-w-[16px] px-1 text-[10px] bg-green-500/30 border-green-500/50">
                  {
                    inboxStore.items.filter((item) => item.type === "textures")
                      .length
                  }
                </Badge>
              </TabsTrigger>
              <TabsTrigger
                value="models"
                className="data-[state=active]:bg-purple-500/20 data-[state=active]:text-purple-300 text-xs"
              >
                Models
                <Badge className="ml-1 h-4 min-w-[16px] px-1 text-[10px] bg-purple-500/30 border-purple-500/50">
                  {
                    inboxStore.items.filter((item) => item.type === "models")
                      .length
                  }
                </Badge>
              </TabsTrigger>
            </TabsList>
          </Tabs>

          {/* Filtered Items List */}
          {(() => {
            const filteredItems = inboxStore.items.filter(
              (item) => item.type === inboxFilter
            );

            if (filteredItems.length === 0) {
              return (
                <div className="text-center py-8 text-white/40">
                  <Inbox className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No {inboxFilter} in inbox</p>
                  <p className="text-xs mt-1">Click assets to add them</p>
                </div>
              );
            }

            return (
              <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                {filteredItems.map((item) => (
                  <div
                    key={item.id}
                    className="flex items-center gap-3 p-2 bg-white/5 rounded-lg border border-white/10 hover:bg-white/10 transition-colors"
                  >
                    <img
                      src={item.asset.thumbnail_url}
                      alt={item.name}
                      className="w-12 h-12 object-cover rounded"
                    />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {item.name}
                      </p>
                      <p className="text-xs text-white/60 capitalize">
                        {item.type}
                      </p>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => {
                        inboxStore.removeItem(item.id);
                        toast.info(`Removed ${item.name}`);
                      }}
                      className="h-6 w-6 text-white/40 hover:text-white hover:bg-white/10"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ))}
              </div>
            );
          })()}
        </div>
      </PopoverContent>
    </Popover>
  );
}
