import { BaseNode } from "./BaseNode";
import { SummaryVisuals } from "./summary/SummaryVisuals";
import { SummaryTextual } from "./summary/SummaryTextual";
import { SummaryContext } from "./summary/SummaryContext";
import { useMoodboardStore } from "@/store/moodboardStore";

export function SummaryNode() {
  const moodboard = useMoodboardStore((state) => state.moodboard);

  const images = [
    ...(moodboard.categoryImages?.compositions || []),
    ...(moodboard.categoryImages?.actions || []),
    ...(moodboard.categoryImages?.lighting || []),
    ...(moodboard.categoryImages?.location || []),
  ];

  return (
    <BaseNode
      title="Moodboard Summary"
      showTargetHandle
      titleColor="text-cr8-yellow"
    >
      <div className="space-y-6">
        <SummaryVisuals
          images={images}
          colorPalette={moodboard.colorPalette || []}
        />
        <SummaryTextual
          theme={moodboard.theme}
          storyline={moodboard.storyline}
          keywords={moodboard.keywords}
          tone={moodboard.tone}
        />
        <SummaryContext
          industry={moodboard.industry}
          targetAudience={moodboard.targetAudience}
          usageIntent={moodboard.usageIntent}
        />
      </div>
    </BaseNode>
  );
}
