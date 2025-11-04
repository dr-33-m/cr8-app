import { useState } from "react";
import { PolyHavenAsset } from "@/lib/services/polyhavenService";
import { useAssetBrowser } from "@/hooks/useAssetBrowser";
import { AssetPanelView } from "./AssetPanelView";
import { AssetDialog } from "../dialogs";

interface AssetPanelProps {
  onAssetSelect?: (asset: PolyHavenAsset & { id: string }) => void;
}

export function AssetPanel({ onAssetSelect }: AssetPanelProps) {
  const [dialogOpen, setDialogOpen] = useState(false);

  // Use asset browser hook with compact view settings
  const assetBrowser = useAssetBrowser({
    initialType: "textures",
    initialLimit: 6, // Limit to 6 for compact view
    onAssetSelect,
  });

  const handleShowAll = () => {
    setDialogOpen(true);
  };

  return (
    <>
      <AssetPanelView
        assetBrowser={assetBrowser}
        onShowDialog={handleShowAll}
        onAssetSelect={onAssetSelect}
      />

      {/* Expanded Dialog */}
      <AssetDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        onAssetSelect={onAssetSelect}
        initialType={assetBrowser.selectedType}
      />
    </>
  );
}
