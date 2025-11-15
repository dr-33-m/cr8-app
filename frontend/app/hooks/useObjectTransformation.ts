import { useState, useRef, useCallback, useEffect } from "react";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { toast } from "sonner";
import { v4 as uuidv4 } from "uuid";
import { TransformValue, TransformMode } from "@/lib/types/transformation";
import { hasValuesChanged } from "@/lib/utils";
import useSceneContextStore from "@/store/sceneContextStore";

import { UseObjectTransformationProps } from "@/lib/types/transformation";

export function useObjectTransformation({
  objectName,
  onTransformChange,
}: UseObjectTransformationProps) {
  // Get the current object from scene context store
  const sceneObject = useSceneContextStore((state) =>
    state.getObjectByName(objectName)
  );

  // Initialize state with actual object transform values
  const [move, setMove] = useState<TransformValue>({
    x: sceneObject?.location[0] ?? 0,
    y: sceneObject?.location[1] ?? 0,
    z: sceneObject?.location[2] ?? 0,
  });
  const [rotate, setRotate] = useState<TransformValue>({
    x: sceneObject?.rotation[0] ?? 0,
    y: sceneObject?.rotation[1] ?? 0,
    z: sceneObject?.rotation[2] ?? 0,
  });
  const [scale, setScale] = useState<TransformValue>({
    x: sceneObject?.scale[0] ?? 1,
    y: sceneObject?.scale[1] ?? 1,
    z: sceneObject?.scale[2] ?? 1,
  });
  const [mode, setMode] = useState<TransformMode>("move");
  const { sendMessage, isFullyConnected } = useWebSocketContext();

  // Keep track of last sent values to prevent duplicate commands
  const lastSentValues = useRef<{
    move: TransformValue;
    rotate: TransformValue;
    scale: TransformValue;
  }>({
    move: { x: 0, y: 0, z: 0 },
    rotate: { x: 0, y: 0, z: 0 },
    scale: { x: 1, y: 1, z: 1 },
  });

  // Reinitialize state when objectName changes
  useEffect(() => {
    if (sceneObject) {
      setMove({
        x: sceneObject.location[0],
        y: sceneObject.location[1],
        z: sceneObject.location[2],
      });
      setRotate({
        x: sceneObject.rotation[0],
        y: sceneObject.rotation[1],
        z: sceneObject.rotation[2],
      });
      setScale({
        x: sceneObject.scale[0],
        y: sceneObject.scale[1],
        z: sceneObject.scale[2],
      });
      // Reset last sent values to prevent stale comparisons
      lastSentValues.current = {
        move: {
          x: sceneObject.location[0],
          y: sceneObject.location[1],
          z: sceneObject.location[2],
        },
        rotate: {
          x: sceneObject.rotation[0],
          y: sceneObject.rotation[1],
          z: sceneObject.rotation[2],
        },
        scale: {
          x: sceneObject.scale[0],
          y: sceneObject.scale[1],
          z: sceneObject.scale[2],
        },
      };
    }
  }, [sceneObject]);

  // Update transform change callback when values change
  const updateTransformChange = useCallback(() => {
    if (onTransformChange) {
      onTransformChange({ move, rotate, scale });
    }
  }, [move, rotate, scale, onTransformChange]);

  const getCurrentValues = (): TransformValue => {
    switch (mode) {
      case "move":
        return move;
      case "rotate":
        return rotate;
      case "scale":
        return scale;
    }
  };

  const updateCurrentValues = (values: TransformValue) => {
    switch (mode) {
      case "move":
        setMove(values);
        // Only send command if values actually changed
        if (hasValuesChanged(values, lastSentValues.current.move)) {
          lastSentValues.current.move = { ...values };
          sendTransformCommand("transform_translate", {
            value_x: values.x,
            value_y: values.y,
            value_z: values.z,
          });
        }
        break;
      case "rotate":
        setRotate(values);
        // Only send command if values actually changed
        if (hasValuesChanged(values, lastSentValues.current.rotate)) {
          lastSentValues.current.rotate = { ...values };
          sendTransformCommand("transform_rotate", {
            value_x: values.x,
            value_y: values.y,
            value_z: values.z,
          });
        }
        break;
      case "scale":
        setScale(values);
        // Only send command if values actually changed
        if (hasValuesChanged(values, lastSentValues.current.scale)) {
          lastSentValues.current.scale = { ...values };
          sendTransformCommand("transform_resize", {
            value_x: values.x,
            value_y: values.y,
            value_z: values.z,
          });
        }
        break;
    }
  };

  const resetCurrentMode = () => {
    switch (mode) {
      case "move":
        const resetMove = { x: 0, y: 0, z: 0 };
        setMove(resetMove);
        lastSentValues.current.move = resetMove;
        break;
      case "rotate":
        const resetRotate = { x: 0, y: 0, z: 0 };
        setRotate(resetRotate);
        lastSentValues.current.rotate = resetRotate;
        break;
      case "scale":
        const resetScale = { x: 1, y: 1, z: 1 };
        setScale(resetScale);
        lastSentValues.current.scale = resetScale;
        break;
    }
  };

  // Send transformation command to Blender with message_id
  const sendTransformCommand = async (command: string, params: any) => {
    if (!isFullyConnected) {
      toast.error("Not connected to Blender");
      return;
    }

    try {
      const messageId = uuidv4();
      sendMessage({
        addon_id: "multi_registry_assets",
        command: command,
        params: params,
        message_id: messageId,
        route: "direct", // Direct command to Blender
      });
    } catch (error) {
      toast.error(`Failed to send transformation: ${error}`);
    }
  };

  return {
    // State
    move,
    rotate,
    scale,
    mode,
    isFullyConnected,

    // Computed
    currentValues: getCurrentValues(),

    // Actions
    setMode,
    updateCurrentValues,
    resetCurrentMode,
    updateTransformChange,
  };
}
