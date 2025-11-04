"use client";

import React, { useState, useEffect } from "react";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { Move3D, Scale3d, Rotate3d, Move3d } from "lucide-react";
import { cn } from "@/lib/utils";
import { TransformValue, TransformMode } from "@/lib/types/transformation";
import { useObjectTransformation } from "@/hooks/useObjectTransformation";
import { ObjectTransformationScrollbar } from "./ObjectTransformationScrollbar";

interface ObjectTransformationPopoverProps {
  objectName: string;
  onTransformChange?: (transforms: {
    move: TransformValue;
    rotate: TransformValue;
    scale: TransformValue;
  }) => void;
}

export const ObjectTransformationPopover: React.FC<
  ObjectTransformationPopoverProps
> = ({ objectName, onTransformChange }) => {
  const [isPopoverOpen, setIsPopoverOpen] = useState(false);

  const {
    move,
    rotate,
    scale,
    mode,
    currentValues,
    setMode,
    updateCurrentValues,
    resetCurrentMode,
    updateTransformChange,
  } = useObjectTransformation({
    objectName,
    onTransformChange,
  });

  // Update transform change callback when values change
  useEffect(() => {
    updateTransformChange();
  }, [move, rotate, scale, updateTransformChange]);

  return (
    <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
      <PopoverTrigger>
        <Button variant="ghost" size="icon" className="h-6 w-6">
          <Move3D className="h-3 w-3" />
        </Button>
      </PopoverTrigger>
      <PopoverContent
        className="w-72 p-4 bg-background border border-border shadow-lg"
        align="start"
        sideOffset={8}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-semibold">Transform: {objectName}</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                resetCurrentMode();
              }}
              className="h-6 px-2 text-xs"
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
            <ObjectTransformationScrollbar
              label="X"
              value={currentValues.x}
              onChange={(x) => updateCurrentValues({ ...currentValues, x })}
              mode={mode}
            />
            <ObjectTransformationScrollbar
              label="Y"
              value={currentValues.y}
              onChange={(y) => updateCurrentValues({ ...currentValues, y })}
              mode={mode}
            />
            <ObjectTransformationScrollbar
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
