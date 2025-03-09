import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import { Animation } from "@/lib/types/animations";
import { AnimationCard } from "./AnimationCard";
import { ChevronLeft, ChevronRight } from "lucide-react";

interface AnimationDialogProps {
  animations: Animation[];
  animationType: "camera" | "light" | "product";
  targetEmpty: string | null;
  onClose: () => void;
}

export function AnimationDialog({
  animations,
  animationType,
  targetEmpty,
  onClose,
}: AnimationDialogProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 8; // More items per page in the dialog

  const totalPages = Math.ceil(animations.length / itemsPerPage);

  const displayedAnimations = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return animations.slice(startIndex, startIndex + itemsPerPage);
  }, [animations, currentPage]);

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-medium">
          {animationType.charAt(0).toUpperCase() + animationType.slice(1)}{" "}
          Animations
        </h2>
      </div>

      {/* Animation grid - larger grid (4 columns) */}
      <div className="grid grid-cols-4 gap-3">
        {displayedAnimations.map((animation) => (
          <AnimationCard
            key={animation.id}
            animation={animation}
            targetEmpty={targetEmpty}
            isSelected={false}
          />
        ))}
      </div>

      {/* Pagination controls */}
      <div className="flex justify-between items-center">
        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>

        <span className="text-sm">
          Page {currentPage} of {totalPages}
        </span>

        <Button
          variant="outline"
          size="sm"
          onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
          disabled={currentPage === totalPages}
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </div>

      <Button variant="default" onClick={onClose} className="w-full">
        Close
      </Button>
    </div>
  );
}
