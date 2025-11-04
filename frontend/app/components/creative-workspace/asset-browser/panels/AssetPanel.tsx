import { useState } from "react";
import { useAssetBrowser } from "@/hooks/useAssetBrowser";
import { AssetPanelView } from "./AssetPanelView";
import { AssetDialog } from "../dialogs";
import { AssetPanelProps } from "@/lib/types/assetBrowser";

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
