import { Button } from "@/components/ui/button";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { useAssetPlacerStore } from "@/store/assetPlacerStore";
import { AssetItem } from "./AssetItem";

// No props needed as we use the store for state management
export function AssetSelection() {
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
        <Tabs defaultValue="Assets" className="w-full">
          <TabsList className="grid w-full grid-cols-3 mb-4 bg-white/5">
            <TabsTrigger
              value="Assets"
              className="data-[state=active]:bg-[#0077B6] data-[state=active]:text-white"
            >
              Assets
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
          <TabsContent value="Assets" className="grid grid-cols-3 gap-2">
            {useAssetPlacerStore((state) => state.availableAssets).map(
              (asset) => (
                <AssetItem key={asset.id} asset={asset} />
              )
            )}
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
