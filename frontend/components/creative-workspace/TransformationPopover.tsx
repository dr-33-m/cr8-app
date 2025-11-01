"use client";

import React, { useState, useRef, useCallback } from "react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Move3D, Scale3d, Rotate3d, Move3d } from "lucide-react";
import { cn } from "@/lib/utils";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { toast } from "sonner";
import { v4 as uuidv4 } from "uuid";

interface TransformationPopoverProps {
  objectName: string;
  onTransformChange?: (transforms: {
    move: TransformValue;
    rotate: TransformValue;
    scale: TransformValue;
  }) => void;
}

interface TransformValue {
  x: number;
  y: number;
  z: number;
}

type TransformMode = "move" | "rotate" | "scale";

interface AppleScrollbarProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  mode: TransformMode;
}

const AppleScrollbar: React.FC<AppleScrollbarProps> = ({
  label,
  value,
  onChange,
  mode,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const trackRef = useRef<HTMLDivElement>(null);
  const dragStartRef = useRef<{ value: number; clientX: number } | null>(null);

  // Use refs to store the latest values without causing re-renders
  const valueRef = useRef(value);
  const onChangeRef = useRef(onChange);

  // Update refs when props change
  React.useEffect(() => {
    valueRef.current = value;
    onChangeRef.current = onChange;
  }, [value, onChange]);

  const getStep = useCallback(() => {
    switch (mode) {
      case "move":
        return 0.1;
      case "rotate":
        return 0.1;
      case "scale":
        return 0.1;
    }
  }, [mode]);

  const getThumbPosition = () => {
    const step = getStep();
    const range = step * 100;
    const normalizedValue = Math.max(-range, Math.min(range, value));
    return 50 + (normalizedValue / range) * 40;
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    setIsDragging(true);
    dragStartRef.current = {
      value: value,
      clientX: e.clientX,
    };
  };

  // Use stable references for event handlers
  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!dragStartRef.current) return;

      const deltaX = e.clientX - dragStartRef.current.clientX;
      const sensitivity = getStep() / 2;
      const newValue = dragStartRef.current.value + deltaX * sensitivity;

      const step = getStep();
      const roundedValue = Number.parseFloat(
        newValue.toFixed(step < 1 ? 1 : 0)
      );

      // Only call onChange if value actually changed
      if (roundedValue !== valueRef.current) {
        onChangeRef.current(roundedValue);
      }
    },
    [getStep]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    dragStartRef.current = null;
  }, []);

  // Handle global mouse events for dragging
  React.useEffect(() => {
    if (!isDragging) return;

    const handleDocumentMouseMove = (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      handleMouseMove(e);
    };

    const handleDocumentMouseUp = (e: MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      handleMouseUp();
    };

    // Prevent text selection while dragging
    document.body.style.userSelect = "none";
    document.body.style.cursor = "ew-resize";

    document.addEventListener("mousemove", handleDocumentMouseMove);
    document.addEventListener("mouseup", handleDocumentMouseUp);

    return () => {
      document.body.style.userSelect = "";
      document.body.style.cursor = "";
      document.removeEventListener("mousemove", handleDocumentMouseMove);
      document.removeEventListener("mouseup", handleDocumentMouseUp);
    };
  }, [isDragging, handleMouseMove, handleMouseUp]);

  const handleDoubleClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onChange(mode === "scale" ? 1 : 0);
  };

  const getTickOffset = () => {
    const step = getStep();
    return -(value / step) * 8;
  };

  const generateMovingTicks = () => {
    const ticks: JSX.Element[] = [];
    const step = getStep();
    const tickOffset = getTickOffset();
    const trackWidth = 200;
    const tickSpacing = 12;

    const visibleRange = trackWidth / tickSpacing;
    const centerTickIndex = Math.round(value / step);
    const startIndex = centerTickIndex - Math.ceil(visibleRange / 2) - 5;
    const endIndex = centerTickIndex + Math.ceil(visibleRange / 2) + 5;

    for (let i = startIndex; i <= endIndex; i++) {
      const position = 50 + ((i * tickSpacing + tickOffset) / trackWidth) * 100;

      if (position < -5 || position > 105) continue;

      const tickValue = i * step;
      const isMajor =
        Math.abs(tickValue) % (step * 5) < 0.001 || Math.abs(tickValue) < 0.001;

      const distanceFromCenter = Math.abs(position - 50);
      const isActive = distanceFromCenter < 3;

      ticks.push(
        <div
          key={i}
          className={cn(
            "absolute top-1/2 transform -translate-x-1/2 -translate-y-1/2 transition-all duration-200",
            isActive
              ? isMajor
                ? "h-5 w-[1.5px] bg-primary/90 shadow-xs scale-110"
                : "h-3 w-0.5 bg-primary/80 scale-110"
              : isMajor
                ? "h-4 w-0.5 bg-muted-foreground/50"
                : "h-2 w-px bg-muted-foreground/30",
            (isHovered || isDragging) && !isActive && "opacity-70"
          )}
          style={{ left: `${position}%` }}
        />
      );
    }
    return ticks;
  };

  return (
    <div className="flex items-center justify-between py-2">
      <label className="text-sm font-medium text-muted-foreground min-w-[12px]">
        {label}
      </label>
      <div className="flex items-center gap-3 flex-1 ml-4">
        <div
          ref={trackRef}
          className={cn(
            "relative flex-1 h-7 bg-muted rounded-sm overflow-hidden transition-all duration-200 cursor-ew-resize select-none border border-border",
            (isHovered || isDragging) && "bg-muted/80 border-border/80"
          )}
          onMouseEnter={() => !isDragging && setIsHovered(true)}
          onMouseLeave={() => !isDragging && setIsHovered(false)}
          onMouseDown={handleMouseDown}
          onDoubleClick={handleDoubleClick}
        >
          {generateMovingTicks()}
          <div className="absolute top-1/2 left-1/2 w-px h-3 bg-muted-foreground/20 transform -translate-x-1/2 -translate-y-1/2" />
        </div>
        <div className="w-12 text-right">
          <span className="text-sm font-mono text-foreground">
            {value.toFixed(getStep() < 1 ? 1 : 0)}
          </span>
        </div>
      </div>
    </div>
  );
};

export const TransformationPopover: React.FC<TransformationPopoverProps> = ({
  objectName,
  onTransformChange,
}) => {
  const [move, setMove] = useState<TransformValue>({ x: 0, y: 0, z: 0 });
  const [rotate, setRotate] = useState<TransformValue>({ x: 0, y: 0, z: 0 });
  const [scale, setScale] = useState<TransformValue>({ x: 1, y: 1, z: 1 });
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

  React.useEffect(() => {
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

  // Helper function to check if values have actually changed
  const hasValuesChanged = (
    newValues: TransformValue,
    oldValues: TransformValue
  ): boolean => {
    return (
      Math.abs(newValues.x - oldValues.x) > 0.001 ||
      Math.abs(newValues.y - oldValues.y) > 0.001 ||
      Math.abs(newValues.z - oldValues.z) > 0.001
    );
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
        type: "addon_command",
        addon_id: "multi_registry_assets",
        command: command,
        params: params,
        message_id: messageId,
      });
    } catch (error) {
      toast.error(`Failed to send transformation: ${error}`);
    }
  };

  const currentValues = getCurrentValues();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="h-6 w-6 text-muted-foreground hover:text-foreground hover:bg-accent"
          onClick={(e) => e.stopPropagation()}
        >
          <Move3D className="h-3 w-3" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-72 p-4 bg-popover shadow-xl border"
        align="start"
        sideOffset={8}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold text-foreground">
              Transform: {objectName}
            </h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                resetCurrentMode();
              }}
              className="h-6 px-2 text-xs text-muted-foreground hover:text-foreground"
            >
              Reset
            </Button>
          </div>

          <div className="flex gap-1 p-1 bg-muted/20 rounded-lg">
            <Button
              variant={mode === "move" ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setMode("move");
              }}
              className={cn(
                "flex-1 h-8 px-2 transition-all duration-200",
                mode === "move"
                  ? "bg-primary/30 shadow-xs text-foreground border border-primary/80"
                  : "text-muted-foreground"
              )}
            >
              <Move3d className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant={mode === "rotate" ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setMode("rotate");
              }}
              className={cn(
                "flex-1 h-8 px-2 transition-all duration-200",
                mode === "rotate"
                  ? "bg-primary/30 shadow-xs text-foreground border border-primary/80"
                  : "text-muted-foreground"
              )}
            >
              <Rotate3d className="w-3.5 h-3.5" />
            </Button>
            <Button
              variant={mode === "scale" ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                setMode("scale");
              }}
              className={cn(
                "flex-1 h-8 px-2 transition-all duration-200",
                mode === "scale"
                  ? "bg-primary/30 shadow-xs text-foreground border border-primary/80"
                  : "text-muted-foreground"
              )}
            >
              <Scale3d className="w-3.5 h-3.5" />
            </Button>
          </div>
          <div className="space-y-1">
            <AppleScrollbar
              label="X"
              value={currentValues.x}
              onChange={(x) => updateCurrentValues({ ...currentValues, x })}
              mode={mode}
            />
            <AppleScrollbar
              label="Y"
              value={currentValues.y}
              onChange={(y) => updateCurrentValues({ ...currentValues, y })}
              mode={mode}
            />
            <AppleScrollbar
              label="Z"
              value={currentValues.z}
              onChange={(z) => updateCurrentValues({ ...currentValues, z })}
              mode={mode}
            />
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
};
