import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { useAssetBrowser } from "@/hooks/useAssetBrowser";
import { AssetDialogView } from "./AssetDialogView";
import polyhaveLogo from "@/assets/polyhaven_256.png";
import { AssetDialogProps } from "@/lib/types/assetBrowser";

export function AssetDialog({
  open,
  onOpenChange,
  onAssetSelect,
  initialType = "textures",
}: AssetDialogProps) {
  // Use asset browser hook with dialog settings
  const assetBrowser = useAssetBrowser({
    initialType,
    initialLimit: 20, // Full pagination for dialog
    onAssetSelect,
    enabled: open, // Only enable when dialog is open
  });

  // Reset to initial type when dialog opens
  const handleOpenChange = (isOpen: boolean) => {
    onOpenChange(isOpen);
    if (isOpen && initialType) {
      assetBrowser.setType(initialType as any);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-7xl! h-[90vh]!">
        <DialogHeader className="shrink-0">
          <div className="flex items-center gap-2">
            <img src={polyhaveLogo} alt="Poly Haven" className="w-8 h-8" />
            <DialogTitle>Poly Haven Assets</DialogTitle>
          </div>
        </DialogHeader>

        <AssetDialogView
          onAssetSelect={onAssetSelect}
          initialType={initialType}
        />
      </DialogContent>
    </Dialog>
  );
}
