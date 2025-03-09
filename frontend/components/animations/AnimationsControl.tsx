import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Dialog, DialogContent, DialogTrigger } from "@/components/ui/dialog";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { useAnimationStore } from "@/store/animationStore";
import { useTemplateControlsStore } from "@/store/TemplateControlsStore";
import { useAssetPlacerStore } from "@/store/assetPlacerStore";
import { AnimationCard } from "./AnimationCard";
import { AnimationDialog } from "./AnimationDialog";

export function AnimationsControl() {
  // Animation type filter
  const [selectedType, setSelectedType] = useState<
    "camera" | "light" | "product"
  >("camera");

  // Pagination
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 4;

  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);

  // Target empty selection
  const [selectedEmpty, setSelectedEmpty] = useState<string | null>(null);

  // Get animations from store
  const { animations } = useAnimationStore();

  // Get empties
  const controls = useTemplateControlsStore((state) => state.controls);
  const placedAssets = useAssetPlacerStore((state) => state.placedAssets);

  // Filtered animations for the selected type
  const filteredAnimations = useMemo(() => {
    // Map product_animation to product for consistency with our UI
    if (selectedType === "product") {
      return animations.product || [];
    }
    return animations[selectedType] || [];
  }, [animations, selectedType]);

  // Total pages
  const totalPages = Math.ceil(filteredAnimations.length / itemsPerPage);

  // Paginated animations for current view
  const displayedAnimations = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return filteredAnimations.slice(startIndex, startIndex + itemsPerPage);
  }, [filteredAnimations, currentPage]);

  // Get appropriate empties based on animation type
  const availableEmpties = useMemo(() => {
    const allEmpties = (controls?.objects || [])
      .filter((obj) => obj.object_type === "EMPTY")
      .map((obj) => obj.name);

    // For product animations, only use empties with products
    if (selectedType === "product") {
      return allEmpties.filter((emptyName) =>
        placedAssets.some((asset) => asset.emptyName === emptyName)
      );
    }

    return allEmpties;
  }, [controls, placedAssets, selectedType]);

  // Auto-select first empty if available and none selected
  useMemo(() => {
    if (availableEmpties.length > 0 && !selectedEmpty) {
      setSelectedEmpty(availableEmpties[0]);
    } else if (availableEmpties.length === 0) {
      setSelectedEmpty(null);
    }
  }, [availableEmpties, selectedEmpty]);

  return (
    <div className="space-y-4">
      {/* Filter controls */}
      <div className="flex justify-between gap-2">
        <Select
          value={selectedType}
          onValueChange={(value) => {
            setSelectedType(value as "camera" | "light" | "product");
            setCurrentPage(1); // Reset to first page on type change
          }}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Animation type" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="camera">Camera</SelectItem>
            <SelectItem value="light">Light</SelectItem>
            <SelectItem value="product">Product</SelectItem>
          </SelectContent>
        </Select>

        <Select
          value={selectedEmpty || ""}
          onValueChange={setSelectedEmpty}
          disabled={availableEmpties.length === 0}
        >
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="Select target" />
          </SelectTrigger>
          <SelectContent>
            {availableEmpties.map((empty) => (
              <SelectItem key={empty} value={empty}>
                {empty.replace("controllable_", "")}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      {/* No empties warning */}
      {availableEmpties.length === 0 && (
        <div className="text-xs text-yellow-400 bg-yellow-400/10 p-2 rounded">
          {selectedType === "product"
            ? "No product empties available. Place a product first."
            : "No empties available."}
        </div>
      )}

      {/* Animation grid */}
      <div className="grid grid-cols-2 gap-2">
        {displayedAnimations.map((animation) => (
          <AnimationCard
            key={animation.id}
            animation={animation}
            targetEmpty={selectedEmpty}
            isSelected={false}
          />
        ))}

        {filteredAnimations.length === 0 && (
          <div className="col-span-2 text-center text-xs text-white/60 py-4">
            No animations available
          </div>
        )}
      </div>

      {/* Pagination controls */}
      {filteredAnimations.length > 0 && (
        <div className="flex justify-between items-center">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>

          <span className="text-xs">
            Page {currentPage} of {Math.min(totalPages, 3)}
          </span>

          <Button
            variant="outline"
            size="sm"
            onClick={() =>
              setCurrentPage((p) => Math.min(3, totalPages, p + 1))
            }
            disabled={
              currentPage === Math.min(3, totalPages) || totalPages === 0
            }
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Show all button (only if more than 12 animations) */}
      {filteredAnimations.length > 12 && (
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button variant="outline" className="w-full">
              Show All Animations
            </Button>
          </DialogTrigger>
          <DialogContent className="sm:max-w-[600px]">
            <AnimationDialog
              animations={filteredAnimations}
              animationType={selectedType}
              targetEmpty={selectedEmpty}
              onClose={() => setDialogOpen(false)}
            />
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
}
