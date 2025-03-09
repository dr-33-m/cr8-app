import React, { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useAnimationStore } from "@/store/animationStore";
import { useAnimations } from "@/hooks/useAnimations";
import { AnimationCard } from "./AnimationCard";
import { toast } from "sonner";

interface AnimationSectionProps {
  type: "camera" | "light" | "product";
  label: string;
  empties: string[];
}

export function AnimationSection({
  type,
  label,
  empties,
}: AnimationSectionProps) {
  const { animations, selectedAnimations, selectAnimation } =
    useAnimationStore();
  const [selectedEmpty, setSelectedEmpty] = useState<string | null>(null);
  const { applyAnimation } = useAnimations();

  // Use a ref to track if we've already done the initial selection
  const initialSelectionDone = useRef(false);

  // Get all animations for this type
  const typeAnimations = animations[type] || [];

  // Get the currently selected animation ID for this type
  const selectedAnimationId = selectedAnimations[type];

  // Find the full animation object
  const selectedAnimation = typeAnimations.find(
    (a) => a.id === selectedAnimationId
  );

  // Track if we can apply (need both animation and empty)
  const canApply = !!selectedAnimationId && !!selectedEmpty;

  // Auto-select first empty ONLY on initial render or when empties change
  // and we haven't selected anything yet
  useEffect(() => {
    if (empties.length > 0 && !selectedEmpty && !initialSelectionDone.current) {
      initialSelectionDone.current = true;
      setSelectedEmpty(empties[0]);
    }
  }, [empties]); // Careful: don't include selectedEmpty in dependencies

  // Reset selection when no empties are available
  useEffect(() => {
    if (empties.length === 0 && selectedEmpty) {
      setSelectedEmpty(null);
      initialSelectionDone.current = false; // Reset tracking ref
    }
  }, [empties, selectedEmpty]);

  const handleApplyAnimation = () => {
    if (!selectedAnimation || !selectedEmpty) return;

    applyAnimation(selectedAnimation, selectedEmpty);
    const displayName = selectedEmpty.replace("controllable_", "");
    toast.success(`Applied ${type} animation to ${displayName}`);
  };

  return (
    <div className="space-y-3">
      <div className="flex justify-between items-center">
        <h3 className="text-sm font-medium">{label}</h3>

        {/* Empty selector */}
        {empties.length > 0 && (
          <Select
            value={selectedEmpty || ""}
            onValueChange={setSelectedEmpty}
            disabled={empties.length === 0}
          >
            <SelectTrigger className="w-32 h-7 text-xs">
              <SelectValue placeholder="Select target" />
            </SelectTrigger>
            <SelectContent>
              {empties.map((empty) => (
                <SelectItem key={empty} value={empty}>
                  {empty.replace("controllable_", "")}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      </div>

      {/* No empties message */}
      {empties.length === 0 && (
        <div className="text-xs text-yellow-400 bg-yellow-400/10 p-2 rounded">
          {type === "product"
            ? "No product empties available. Place a product first."
            : "No empties available."}
        </div>
      )}

      {/* Animations grid */}
      <div className="grid grid-cols-2 gap-2">
        {typeAnimations.map((animation) => (
          <AnimationCard
            key={animation.id}
            animation={animation}
            isSelected={selectedAnimationId === animation.id}
            onSelect={(id) => selectAnimation(type, id)}
          />
        ))}

        {typeAnimations.length === 0 && (
          <div className="col-span-2 text-center text-xs text-white/60 py-4">
            No animations available
          </div>
        )}
      </div>

      {/* Apply button */}
      <Button
        onClick={handleApplyAnimation}
        disabled={!canApply}
        size="sm"
        className="w-full"
      >
        Apply Animation
      </Button>
    </div>
  );
}
