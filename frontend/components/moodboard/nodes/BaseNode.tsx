import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Handle, Position } from "reactflow";
import { cn } from "@/lib/utils";
import { ReactNode } from "react";

interface BaseNodeProps {
  title: string;
  children: ReactNode;
  className?: string;
  showSourceHandle?: boolean;
  showTargetHandle?: boolean;
  titleColor?: string;
}

export function BaseNode({
  title,
  children,
  className,
  showSourceHandle = false,
  showTargetHandle = false,
  titleColor = "text-white",
}: BaseNodeProps) {
  return (
    <Card className={cn("min-w-[300px] shadow-xl", className)}>
      {showTargetHandle && <Handle type="target" position={Position.Left} />}
      <CardHeader>
        <CardTitle className={titleColor}>{title}</CardTitle>
      </CardHeader>
      <CardContent>{children}</CardContent>
      {showSourceHandle && <Handle type="source" position={Position.Right} />}
    </Card>
  );
}
