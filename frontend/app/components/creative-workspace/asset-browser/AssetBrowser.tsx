import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { AssetPanel } from "./panels";

export function AssetBrowser() {
  const isVisible = useVisibilityStore(
    (state) => state.isAssetSelectionVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleAssetSelection
  );
  return (
    <div
      className={`absolute right-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 
      ${isVisible ? "translate-x-0" : "translate-x-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -left-12 top-0"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronRight className="h-6 w-6" />
        ) : (
          <ChevronLeft className="h-6 w-6" />
        )}
      </Button>
      <Card className="w-96 max-h-[80vh] overflow-y-auto">
        <CardHeader>
          <CardTitle>Asset Browser</CardTitle>
        </CardHeader>
        <CardContent>
          <AssetPanel />
        </CardContent>
      </Card>
    </div>
  );
}
