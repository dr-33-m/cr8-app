import React from "react";
import { Animation } from "@/lib/types/animations";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Button } from "@/components/ui/button";
import { useAnimations } from "@/hooks/useAnimations";
import { toast } from "sonner";
import { useAnimationStore } from "@/store/animationStore";

interface AnimationCardProps {
  animation: Animation;
  isSelected: boolean;
  targetEmpty?: string | null;
  onSelect?: (id: string) => void;
}

export function AnimationCard({
  animation,
  isSelected,
  targetEmpty,
  onSelect,
}: AnimationCardProps) {
  const { applyAnimation } = useAnimations();
  const { selectAnimation } = useAnimationStore();

  const handleApply = () => {
    if (!targetEmpty) {
      toast.error("No target selected");
      return;
    }

    applyAnimation(animation, targetEmpty);
    // Also update the selected animation in the store
    // Convert template_type to the format expected by selectAnimation
    const animationType =
      animation.template_type === "product_animation"
        ? "product"
        : (animation.template_type as "camera" | "light");

    selectAnimation(animationType, animation.id);
    toast.success(`Applied ${animation.name}`);
  };

  const handleCardClick = () => {
    if (onSelect) {
      onSelect(animation.id);
    }
  };

  return (
    <Popover>
      <PopoverTrigger asChild>
        <div
          className={`relative rounded-md overflow-hidden cursor-pointer transition-all
            ${isSelected ? "ring-2 ring-primary" : "hover:ring-1 ring-white/30"}`}
          onClick={handleCardClick}
        >
          {/* Thumbnail with fallback */}
          <div className="aspect-video bg-black/20 relative">
            {animation.thumbnail ? (
              <img
                src={animation.thumbnail}
                alt={animation.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-black/40">
                <span className="text-xs text-white/60">No preview</span>
              </div>
            )}
          </div>

          {/* Animation name */}
          <div className="p-2 bg-black/60">
            <h4 className="text-sm font-medium truncate">{animation.name}</h4>
          </div>
        </div>
      </PopoverTrigger>

      <PopoverContent className="w-72 p-0">
        <div className="space-y-2">
          {/* Larger thumbnail */}
          <div className="aspect-video bg-black/20 relative">
            {animation.thumbnail ? (
              <img
                src={animation.thumbnail}
                alt={animation.name}
                className="w-full h-full object-cover"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center bg-black/40">
                <span className="text-sm text-white/60">No preview</span>
              </div>
            )}
          </div>

          <div className="p-4 space-y-3">
            <h3 className="font-medium">{animation.name}</h3>
            <p className="text-sm text-white/70">
              {animation.template_type.replace("_", " ")}
            </p>

            <Button
              className="w-full"
              onClick={handleApply}
              disabled={!targetEmpty}
            >
              Apply Animation
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  );
}
