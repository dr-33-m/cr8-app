import { Industry, UsageIntent } from "@/lib/types/moodboard";
import { Badge } from "@/components/ui/badge";
import { Building2, Users, Target } from "lucide-react";

interface SummaryContextProps {
  industry?: Industry;
  targetAudience?: string;
  usageIntent?: UsageIntent;
}

export function SummaryContext({
  industry,
  targetAudience,
  usageIntent,
}: SummaryContextProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-white">Context Elements</h3>

      <div className="space-y-3">
        {industry && (
          <div className="flex items-center gap-2">
            <Building2 className="h-4 w-4 text-blue-400" />
            <Badge variant="outline">{industry}</Badge>
          </div>
        )}

        {targetAudience && (
          <div className="flex items-center gap-2">
            <Users className="h-4 w-4 text-blue-400" />
            <span className="text-xs text-white">{targetAudience}</span>
          </div>
        )}

        {usageIntent && (
          <div className="flex items-center gap-2">
            <Target className="h-4 w-4 text-blue-400" />
            <Badge variant="outline">
              {usageIntent
                .split("-")
                .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
                .join(" ")}
            </Badge>
          </div>
        )}
      </div>
    </div>
  );
}
