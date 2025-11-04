import React, { useState, useRef, useCallback } from "react";
import { cn } from "@/lib/utils";
import { ObjectTransformationScrollbarProps } from "@/lib/types/transformation";

export const ObjectTransformationScrollbar: React.FC<
  ObjectTransformationScrollbarProps
> = ({ label, value, onChange, mode }) => {
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
