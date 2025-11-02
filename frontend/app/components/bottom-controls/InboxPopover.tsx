import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
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
      <PopoverTrigger>
        <Button variant="ghost" size="icon" className="relative h-6 w-6">
          <Inbox className="h-4 w-4" />
          {inboxCount > 0 && (
            <Badge className="absolute -top-2 -right-2 h-4 min-w-[16px] px-1 text-[10px] bg-primary border-primary">
              {inboxCount}
            </Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" side="top" align="end">
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
                className="text-xs"
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
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="hdris">
                HDRIs
                <Badge className="ml-1 h-4 min-w-[16px] px-1 text-[10px]">
                  {
                    inboxStore.items.filter((item) => item.type === "hdris")
                      .length
                  }
                </Badge>
              </TabsTrigger>
              <TabsTrigger value="textures">
                Textures
                <Badge className="ml-1 h-4 min-w-[16px] px-1 text-[10px]">
                  {
                    inboxStore.items.filter((item) => item.type === "textures")
                      .length
                  }
                </Badge>
              </TabsTrigger>
              <TabsTrigger value="models">
                Models
                <Badge className="ml-1 h-4 min-w-[16px] px-1 text-[10px]">
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
                <div className="text-center py-8 text-muted-foreground">
                  <Inbox className="h-12 w-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No {inboxFilter} in inbox</p>
                  <p className="text-xs mt-1">Click assets to add them</p>
                </div>
              );
            }

            return (
              <div className="space-y-2 max-h-[280px] overflow-y-auto pr-1">
                {filteredItems.map((item) => (
                  <Card
                    key={item.id}
                    className="flex items-center gap-3 p-2 hover:bg-muted/50 transition-colors"
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
                      <p className="text-xs text-muted-foreground capitalize">
                        {item.type}
                      </p>
                    </div>
                    <Button
                      variant="destructive"
                      size="icon"
                      onClick={() => {
                        inboxStore.removeItem(item.id);
                        toast.info(`Removed ${item.name}`);
                      }}
                      className="h-6 w-6"
                    >
                      <X className="h-3 w-3" />
                    </Button>
                  </Card>
                ))}
              </div>
            );
          })()}
        </div>
      </PopoverContent>
    </Popover>
  );
}
