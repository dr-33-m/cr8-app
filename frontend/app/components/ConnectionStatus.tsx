import { cn } from "@/lib/utils";
import { ConnectionStatusProps } from "@/lib/types/components";

export function ConnectionStatus({ status }: ConnectionStatusProps) {
  const getStatusColor = () => {
    switch (status) {
      case "connected":
        return "bg-green-500";
      case "connecting":
        return "bg-primary animate-pulse";
      case "disconnected":
        return "bg-destructive";
      default:
        return "bg-secondary";
    }
  };

  const getStatusText = () => {
    switch (status) {
      case "connected":
        return "Connected";
      case "connecting":
        return "Connecting...";
      case "disconnected":
        return "Disconnected";
      default:
        return "Unknown";
    }
  };

  return (
    <div className="flex items-center gap-2">
      <div
        className={cn(
          "w-2.5 h-2.5 rounded-full transition-colors",
          getStatusColor()
        )}
      />
      <span className="text-sm">{getStatusText()}</span>
    </div>
  );
}
