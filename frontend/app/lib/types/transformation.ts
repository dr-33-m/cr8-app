export interface TransformValue {
  x: number;
  y: number;
  z: number;
}

export type TransformMode = "move" | "rotate" | "scale";

export interface ObjectTransformationPopoverProps {
  objectName: string;
  onTransformChange?: (transforms: {
    move: TransformValue;
    rotate: TransformValue;
    scale: TransformValue;
  }) => void;
}

export interface ObjectTransformationScrollbarProps {
  label: string;
  value: number;
  onChange: (value: number) => void;
  mode: TransformMode;
}

// Hook interfaces
export interface UseObjectTransformationProps {
  objectName: string;
  onTransformChange?: (transforms: {
    move: TransformValue;
    rotate: TransformValue;
    scale: TransformValue;
  }) => void;
}
