import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

interface SelectedCategoriesDisplayProps {
  selectedCategories: string[];
  onCategoryRemove: (category: string) => void;
  onClearAll: () => void;
}

export function SelectedCategoriesDisplay({
  selectedCategories,
  onCategoryRemove,
  onClearAll,
}: SelectedCategoriesDisplayProps) {
  if (selectedCategories.length === 0) {
    return null;
  }

  return (
    <div className="flex flex-wrap gap-1">
      {selectedCategories.map((category) => (
        <Badge
          key={category}
          className="bg-accent text-accent-foreground border-accent/30 pr-1"
        >
          {category}
          <Button
            variant="destructive"
            size="icon"
            className="h-4 w-4 ml-1"
            onClick={() => onCategoryRemove(category)}
          >
            <X className="w-3 h-3" />
          </Button>
        </Badge>
      ))}
    </div>
  );
}
