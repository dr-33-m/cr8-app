import { Theme, Tone } from "@/types/moodboard";
import { Badge } from "@/components/ui/badge";

interface SummaryTextualProps {
  theme?: Theme;
  storyline?: string;
  keywords?: string[];
  tone?: Tone;
}

export function SummaryTextual({
  theme,
  storyline,
  keywords,
  tone,
}: SummaryTextualProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-white">Textual Elements</h3>

      <div className="space-y-2">
        {theme && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/60">Theme:</span>
            <Badge variant="outline">{theme}</Badge>
          </div>
        )}

        {tone && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/60">Tone:</span>
            <Badge variant="outline">{tone}</Badge>
          </div>
        )}

        {storyline && (
          <div className="space-y-1">
            <span className="text-xs text-white/60">Storyline:</span>
            <p className="text-xs text-white line-clamp-2">{storyline}</p>
          </div>
        )}

        {keywords && keywords.length > 0 && (
          <div className="flex flex-wrap gap-1">
            {keywords.map((keyword, index) => (
              <Badge key={index} variant="secondary" className="text-[10px]">
                {keyword}
              </Badge>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
