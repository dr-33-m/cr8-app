import { Sparkles } from "lucide-react";
import { EmptyStateProps } from "@/lib/types/components";

export function EmptyState({
  title = "Nothing here yet",
  description = "Get started by adding some content",
  hint = "💡 Use the available tools to add items",
  icon = <Sparkles className="h-16 w-16 mx-auto text-secondary" />,
  className = "",
}: EmptyStateProps) {
  return (
    <div className={`text-center py-8 space-y-4 ${className}`}>
      <div className="text-6xl mb-4">{icon}</div>
      <div>
        <p className="text-lg font-medium">{title}</p>
        <p className="text-sm mt-2">{description}</p>
      </div>
      <div className="bg-secondary border rounded-lg p-3 mt-4">
        <p className="text-xs">{hint}</p>
      </div>
    </div>
  );
}
