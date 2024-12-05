import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface AssetSelectionProps {
  isVisible: boolean;
  isFullscreen: boolean;
  selectedAsset: number | null;
  onSelectAsset: (id: number) => void;
  onToggleVisibility: () => void;
}

export function AssetSelection({
  isVisible,
  isFullscreen,
  selectedAsset,
  onSelectAsset,
  onToggleVisibility,
}: AssetSelectionProps) {
  return (
    <div
      className={`absolute right-4 top-1/2 transform -translate-y-1/2 transition-all duration-300 
      ${isVisible ? "translate-x-0" : "translate-x-full"}
      ${isFullscreen ? "scale-75 origin-right" : ""}
      ${!isFullscreen && isVisible ? "right-0" : ""}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute -left-12 top-0 text-white hover:bg-white/10"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronRight className="h-6 w-6" />
        ) : (
          <ChevronLeft className="h-6 w-6" />
        )}
      </Button>
      <div className="backdrop-blur-md bg-white/5 rounded-lg p-4 w-80">
        <h2 className="text-xl font-semibold mb-4 text-white">Select Assets</h2>
        <Tabs defaultValue="Clothes" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-4 bg-white/5">
            <TabsTrigger
              value="Clothes"
              className="data-[state=active]:bg-[#0077B6] data-[state=active]:text-white"
            >
              Clothing
            </TabsTrigger>
            <TabsTrigger
              value="Venues"
              className="data-[state=active]:bg-[#5C0A98] data-[state=active]:text-white"
            >
              Venues
            </TabsTrigger>
            <TabsTrigger
              value="Performances"
              className="data-[state=active]:bg-[#FF006E] data-[state=active]:text-white"
            >
              Performances
            </TabsTrigger>
          </TabsList>
          <TabsContent value="Clothes" className="grid grid-cols-3 gap-2">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div
                key={i}
                className={`aspect-square bg-white/10 rounded-lg cursor-pointer hover:ring-2 hover:ring-[#FFD100] transition-all ${
                  selectedAsset === i ? "ring-2 ring-[#FFD100]" : ""
                }`}
                onClick={() => onSelectAsset(i)}
                role="button"
                tabIndex={0}
                aria-label={`Select asset ${i}`}
              />
            ))}
          </TabsContent>
          <TabsContent value="Venues">
            <p className="text-white/70">Venues here</p>
          </TabsContent>
          <TabsContent value="Performances">
            <p className="text-white/70">Performances here</p>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
