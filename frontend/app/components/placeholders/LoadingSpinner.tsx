import { cn } from "@/lib/utils";

interface LoadingSpinnerProps {
  fullScreen?: boolean;
  message?: string;
  size?: "sm" | "md" | "lg";
  className?: string;
}

const sizeClasses = {
  sm: "h-6 w-6",
  md: "h-8 w-8",
  lg: "h-12 w-12",
};

export function LoadingSpinner({
  fullScreen = false,
  message = "Loading...",
  size = "md",
  className,
}: LoadingSpinnerProps) {
  const containerClasses = fullScreen
    ? "min-h-screen flex items-center justify-center p-4"
    : "flex items-center justify-center p-4";

  return (
    <div className={cn(containerClasses, className)}>
      <div className="text-center">
        <div
          className={cn(
            "animate-spin rounded-full border-b-2 border-primary mx-auto mb-4",
            sizeClasses[size]
          )}
        />
        <p className="text-muted-foreground">{message}</p>
      </div>
    </div>
  );
}
