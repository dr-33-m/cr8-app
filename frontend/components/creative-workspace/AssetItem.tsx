import { useAssetPlacerStore } from "@/store/assetPlacerStore";
import { Asset } from "@/lib/types/assetPlacer";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { EmptyPositionSelector } from "./EmptyPositionSelector";
import { AssetControls } from "./AssetControls";

interface AssetItemProps {
  asset: Asset;
}

export function AssetItem({ asset }: AssetItemProps) {
  const { selectedAssetId, selectAsset, isAssetPlaced } = useAssetPlacerStore();

  const isSelected = selectedAssetId === asset.id;
  const isPlaced = isAssetPlaced(asset.id);

  return (
    <Popover>
      <PopoverTrigger asChild>
        <div
          className={`aspect-square bg-white/10 rounded-lg cursor-pointer 
            hover:ring-2 hover:ring-[#FFD100] transition-all 
            ${isSelected ? "ring-2 ring-white" : ""}
            ${isPlaced ? "ring-2 ring-[#FFD100]" : ""}`}
          style={{
            backgroundImage: `url(${asset.thumbnailUrl})`,
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
          onClick={() => selectAsset(asset.id)}
          role="button"
          tabIndex={0}
          aria-label={`Select asset ${asset.name}`}
        >
          {/* Asset thumbnail or name */}
          <div className="w-full h-full flex items-center justify-center text-white/70 text-sm">
            {asset.name}
          </div>
        </div>
      </PopoverTrigger>

      <PopoverContent className="w-64 p-4 backdrop-blur-md bg-white/5 border border-white/20 rounded-lg">
        <div className="space-y-4">
          <h3 className="font-medium text-white">{asset.name}</h3>

          {isPlaced ? (
            <AssetControls assetId={asset.id} />
          ) : (
            <EmptyPositionSelector assetId={asset.id} />
          )}
        </div>
      </PopoverContent>
    </Popover>
  );
}
