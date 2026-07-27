import { useMemo, useState } from "react";
import { Button } from "@/components/ui/button";
import {
  ChevronLeft,
  ChevronRight,
  ScanEye,
  Lightbulb,
  Triangle,
  Video,
  Trash2,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { ObjectTransformationPopover } from "@/components/creative-workspace/object-transformation";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { useSceneContext } from "@/hooks/useSceneContext";
import { v4 as uuidv4 } from "uuid";
import { toast } from "sonner";
import { EmptyState } from "@/components/placeholders/EmptyState";
import { AssetSearchInput } from "@/components/creative-workspace/asset-browser/filters";
import { ADDON_IDS } from "@/lib/constants/addons";

export function SceneControls() {
  const isVisible = useVisibilityStore((state) => state.isSceneControlsVisible);
  const toggleVisibility = useVisibilityStore(
    (state) => state.toggleSceneControls
  );
  const { objects, timestamp } = useSceneContext();
  const { sendMessage, isFullyConnected, connectionState } =
    useWebSocketContext();

  const [query, setQuery] = useState("");

  // A scene with a few imported assets in it quickly outgrows the card. Type is
  // matched alongside name so "camera" or "light" narrows to a category without
  // having to know what Blender ended up naming things.
  const filteredObjects = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return objects;
    return objects.filter(
      (obj) =>
        obj.name.toLowerCase().includes(q) || obj.type.toLowerCase().includes(q)
    );
  }, [objects, query]);

  const sendSceneCommand = async (
    command: string,
    params: any,
    refreshContext: boolean = true
  ) => {
    if (!isFullyConnected) {
      toast.error("Not connected to Blender");
      return;
    }

    try {
      const messageId = uuidv4();
      sendMessage({
        addon_id: ADDON_IDS.SETS,
        command: command,
        params: params,
        message_id: messageId,
        refresh_context: refreshContext,
        route: "direct", // Direct command to Blender
      });
    } catch (error) {
      toast.error(`Failed to send scene command: ${error}`);
    }
  };

  const isReconnecting = connectionState === "blender_reconnecting";

  // Determine what to show based on connection state
  const renderContent = () => {
    // "connecting" is the very first attempt, not a failure — saying "Blender
    // Disconnected" there alarms the user while their instance is still launching.
    if (connectionState === "connecting") {
      return (
        <EmptyState
          title="Connecting"
          description="Waiting for your Blender session"
          hint="💡 Scene objects will appear once Blender is ready"
        />
      );
    }

    if (
      connectionState === "blender_disconnected" ||
      connectionState === "disconnected"
    ) {
      return (
        <EmptyState
          title="Blender Disconnected"
          description="Scene controls unavailable"
          hint="💡 Reconnect to Blender to access scene objects"
        />
      );
    }

    if (!isReconnecting && objects.length === 0) {
      return (
        <EmptyState
          title="No Objects"
          description="Scene is currently empty"
          hint="💡 Use B.L.A.Z.E to add objects to your scene"
        />
      );
    }

    const isFiltering = query.trim().length > 0;

    return (
      <div className="space-y-3">
        <div className="text-xs mb-2">
          {isFiltering
            ? `${filteredObjects.length} of ${objects.length} object${
                objects.length !== 1 ? "s" : ""
              }`
            : `${objects.length} object${
                objects.length !== 1 ? "s" : ""
              } in scene`}
          {timestamp > 0 && (
            <span className="block text-[10px] mt-1">
              Updated: {new Date(timestamp * 1000).toLocaleTimeString()}
            </span>
          )}
        </div>

        <AssetSearchInput
          value={query}
          onChange={setQuery}
          onClear={() => setQuery("")}
          placeholder="Search objects..."
          compact
        />

        {filteredObjects.length === 0 && (
          <div className="py-6 text-center text-xs text-muted-foreground">
            No objects match{" "}
            <span className="font-medium">{query.trim()}</span>
          </div>
        )}

        <div className={`space-y-2 max-h-96 overflow-y-auto ${isReconnecting ? "opacity-60" : ""}`}>
          {filteredObjects.map((obj) => (
            <Card
              // Keyed by name alone — Blender object names are unique, and an
              // index-based key would remount every row (closing an open
              // transform popover) each time the filter changes.
              key={obj.name}
              className={`transition-colors ${
                isReconnecting ? "cursor-default" : "cursor-pointer"
              } ${
                obj.active
                  ? "bg-primary/30 border-primary/80"
                  : isReconnecting ? "" : "hover:bg-secondary/10"
              }`}
              onClick={() => {
                if (isReconnecting) return;
                sendSceneCommand(
                  "set_active_object",
                  {
                    object_name: obj.name,
                  },
                  true
                );
              }}
            >
              <CardContent className="flex items-center justify-between p-3">
                <div className="flex items-center gap-2 min-w-0 flex-1">
                  <div className="shrink-0">
                    {obj.type.toLowerCase() === "light" ? (
                      <Lightbulb className="h-4 w-4 text-yellow-400" />
                    ) : obj.type.toLowerCase() === "mesh" ? (
                      <Triangle className="h-4 w-4 text-blue-400" />
                    ) : obj.type.toLowerCase() === "camera" ? (
                      <Video className="h-4 w-4 text-green-400" />
                    ) : (
                      <Triangle className="h-4 w-4 text-gray-400" />
                    )}
                  </div>
                  <div className="min-w-0 flex-1 overflow-hidden">
                    <span className="text-sm font-medium truncate">
                      {obj.name}
                    </span>
                  </div>
                </div>

                <div
                  className="flex items-center gap-1 ml-2"
                  onClick={(e) => e.stopPropagation()}
                >
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6"
                    disabled={isReconnecting}
                    onClick={(e) => {
                      e.stopPropagation();
                      sendSceneCommand("focus_on_active_object", {}, true);
                    }}
                  >
                    <ScanEye className="h-3 w-3" />
                  </Button>
                  <ObjectTransformationPopover
                    objectName={obj.name}
                    onOpen={() =>
                      sendSceneCommand(
                        "set_active_object",
                        { object_name: obj.name },
                        true
                      )
                    }
                  />
                  <Button
                    variant="destructive"
                    size="icon"
                    className="h-6 w-6"
                    disabled={isReconnecting}
                    onClick={(e) => {
                      e.stopPropagation();
                      sendSceneCommand(
                        "delete_object",
                        {
                          object_name: obj.name,
                        },
                        true
                      );
                    }}
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div
      className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 
      ${isVisible ? "translate-x-0" : "-translate-x-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-12 top-1/2 -translate-y-1/2"
        onClick={toggleVisibility}
      >
        {isVisible ? (
          <ChevronLeft className="h-6 w-6" />
        ) : (
          <ChevronRight className="h-6 w-6" />
        )}
      </Button>
      <Card className="w-80 max-h-[80vh] overflow-y-auto">
        <CardHeader>
          <CardTitle>Scene Objects</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">{renderContent()}</CardContent>
      </Card>
    </div>
  );
}
