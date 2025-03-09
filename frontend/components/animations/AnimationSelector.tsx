import React, { useState, useEffect } from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useAnimations } from "@/hooks/useAnimations";
import { Animation } from "@/lib/types/animations";
import { toast } from "sonner";

interface AnimationSelectorProps {
  type: "camera" | "light" | "product";
  onApply?: (animation: Animation) => void;
  targetEmptyName?: string;
  className?: string;
  label?: string;
}

export function AnimationSelector({
  type,
  onApply,
  targetEmptyName,
  className,
  label = "Select Animation",
}: AnimationSelectorProps) {
  const [animations, setAnimations] = useState<Animation[]>([]);
  const [selectedId, setSelectedId] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const { loadAnimations, applyAnimation } = useAnimations();

  useEffect(() => {
    const fetchAnimations = async () => {
      setIsLoading(true);
      try {
        const result = await loadAnimations(type);
        setAnimations(result);

        // Auto-select the first animation if available
        if (result.length > 0 && !selectedId) {
          setSelectedId(result[0].id);
        }
      } catch (error) {
        console.error(`Error loading ${type} animations:`, error);
        toast.error(`Failed to load ${type} animations`);
      } finally {
        setIsLoading(false);
      }
    };

    fetchAnimations();
    // Remove selectedId from dependencies to prevent potential infinite loops
  }, [type, loadAnimations]);

  const handleSelectChange = (value: string) => {
    setSelectedId(value);
  };

  const handleApply = () => {
    if (!selectedId) {
      toast.error("Please select an animation first");
      return;
    }

    if (!targetEmptyName && !onApply) {
      toast.error("No target specified for animation");
      return;
    }

    const selectedAnimation = animations.find((anim) => anim.id === selectedId);
    if (!selectedAnimation) {
      toast.error("Selected animation not found");
      return;
    }

    if (onApply) {
      onApply(selectedAnimation);
    } else if (targetEmptyName) {
      applyAnimation(selectedAnimation, targetEmptyName);
      toast.success(`Applied ${type} animation: ${selectedAnimation.name}`);
    }
  };

  const getTypeLabel = () => {
    switch (type) {
      case "camera":
        return "Camera";
      case "light":
        return "Lighting";
      case "product":
        return "Product";
      default:
        return type;
    }
  };

  return (
    <div
      className={`animation-selector flex flex-col gap-2 ${className || ""}`}
    >
      <div className="flex items-center gap-2">
        <div className="flex-1">
          <Select
            value={selectedId}
            onValueChange={handleSelectChange}
            disabled={isLoading || animations.length === 0}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder={`${label} (${getTypeLabel()})`} />
            </SelectTrigger>
            <SelectContent>
              {animations.map((animation) => (
                <SelectItem key={animation.id} value={animation.id}>
                  {animation.name}
                </SelectItem>
              ))}
              {animations.length === 0 && !isLoading && (
                <SelectItem value="none" disabled>
                  No animations available
                </SelectItem>
              )}
            </SelectContent>
          </Select>
        </div>
        <Button
          onClick={handleApply}
          disabled={!selectedId || isLoading}
          size="sm"
        >
          Apply
        </Button>
      </div>
      {isLoading && (
        <p className="text-xs text-gray-500">Loading animations...</p>
      )}
    </div>
  );
}
