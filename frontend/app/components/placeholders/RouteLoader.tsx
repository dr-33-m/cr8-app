import type { ReactNode } from "react";
import { Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

interface RouteLoaderProps {
  title?: string;
  message?: string;
  icon?: ReactNode;
  className?: string;
}

export function RouteLoader({
  title,
  message = "Loading...",
  icon,
  className,
}: RouteLoaderProps) {
  return (
    <div
      className={cn(
        "min-h-screen flex items-center justify-center p-4",
        className
      )}
    >
      <div className="text-center space-y-3">
        <div className="flex justify-center">
          {icon ?? (
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          )}
        </div>
        {title && (
          <p className="text-lg font-medium">{title}</p>
        )}
        <p className="text-sm text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}
