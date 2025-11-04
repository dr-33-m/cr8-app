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
import useSceneContextStore from "@/store/sceneContextStore";
import { ObjectTransformationPopover } from "@/components/creative-workspace/object-transformation";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { v4 as uuidv4 } from "uuid";
import { toast } from "sonner";
import { EmptyState } from "@/components/placeholders/EmptyState";

export function SceneControls() {
  const isVisible = useVisibilityStore((state) => state.isSceneControlsVisible);
  const toggleVisibility = useVisibilityStore(
    (state) => state.toggleSceneControls
  );
  const { objects, timestamp } = useSceneContextStore();
  const { sendMessage, isFullyConnected } = useWebSocketContext();

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
        type: "addon_command",
        addon_id: "multi_registry_assets",
        command: command,
        params: params,
        message_id: messageId,
        refresh_context: refreshContext,
      });
    } catch (error) {
      toast.error(`Failed to send scene command: ${error}`);
    }
  };

  return (
    <div
      className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 
      ${isVisible ? "translate-x-0" : "-translate-x-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -right-12 top-0"
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
        <CardContent className="space-y-4">
          {objects.length === 0 ? (
            <EmptyState
              title="No Objects"
              description="Scene is currently empty"
              hint="💡 Use B.L.A.Z.E to add objects to your scene"
            />
          ) : (
            <div className="space-y-3">
              <div className="text-xs mb-2">
                {objects.length} object{objects.length !== 1 ? "s" : ""} in
                scene
                {timestamp > 0 && (
                  <span className="block text-[10px] mt-1">
                    Updated: {new Date(timestamp * 1000).toLocaleTimeString()}
                  </span>
                )}
              </div>

              <div className="space-y-2 max-h-96 overflow-y-auto">
                {objects.map((obj, index) => (
                  <Card
                    key={`${obj.name}-${index}`}
                    className={`cursor-pointer transition-colors ${
                      obj.active
                        ? "bg-primary/30 border-primary/80"
                        : "hover:bg-secondary/10"
                    }`}
                    onClick={() => {
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
                          onClick={(e) => {
                            e.stopPropagation();
                            sendSceneCommand(
                              "focus_on_active_object",
                              {},
                              true
                            );
                          }}
                        >
                          <ScanEye className="h-3 w-3" />
                        </Button>
                        <ObjectTransformationPopover objectName={obj.name} />
                        <Button
                          variant="destructive"
                          size="icon"
                          className="h-6 w-6"
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
          )}
        </CardContent>
      </Card>
    </div>
  );
}
