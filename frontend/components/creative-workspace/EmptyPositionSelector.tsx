import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useTemplateControlsStore } from "@/store/TemplateControlsStore";
import { useAssetPlacer } from "@/hooks/useAssetPlacer";

interface EmptyPositionSelectorProps {
  assetId: string;
}

export function EmptyPositionSelector({ assetId }: EmptyPositionSelectorProps) {
  const [selectedEmptyName, setSelectedEmptyName] = useState<string | null>(
    null
  );

  // Get the template controls once
  const controls = useTemplateControlsStore((state) => state.controls);

  // Filter empty objects - memoized so it only recalculates when controls change
  const empties = useMemo(() => {
    return (controls?.objects || []).filter(
      (obj) => obj.object_type === "EMPTY"
    );
  }, [controls]);

  const { placeAsset } = useAssetPlacer();

  return (
    <div className="space-y-4">
      {empties.length === 0 ? (
        <div className="p-2 text-center text-sm text-white/60">
          No placement positions available
        </div>
      ) : (
        <>
          <div className="space-y-2">
            <label className="text-sm font-medium text-white">
              Select Position
            </label>
            <Select onValueChange={(value) => setSelectedEmptyName(value)}>
              <SelectTrigger className="bg-white/10 border-white/20">
                <SelectValue placeholder="Choose position" />
              </SelectTrigger>
              <SelectContent className="bg-[#1C1C1C] border-white/20">
                {empties.map((empty) => (
                  <SelectItem key={empty.name} value={empty.name}>
                    {empty.displayName}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <Button
            className="w-full"
            disabled={!selectedEmptyName}
            onClick={() =>
              selectedEmptyName && placeAsset(assetId, selectedEmptyName)
            }
          >
            Place Asset
          </Button>
        </>
      )}
    </div>
  );
}
