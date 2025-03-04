import { useCallback } from "react";
import { toast } from "sonner";
import { useAssetPlacerStore } from "@/store/assetPlacerStore";
import { useWebSocketContext } from "@/contexts/WebSocketContext";

export function useAssetPlacer() {
  const { sendMessage } = useWebSocketContext();
  const {
    availableAssets,
    placedAssets,
    placeAsset: updatePlacedAssetState,
    removePlacedAsset: removePlacedAssetState,
    updatePlacedAsset: updatePlacedAssetProperties,
    getEmptyNameForAsset,
  } = useAssetPlacerStore();

  const placeAsset = useCallback(
    (assetId: string, emptyName: string) => {
      const asset = availableAssets.find((a) => a.id === assetId);
      if (!asset) {
        toast.error("Asset not found");
        return;
      }

      sendMessage({
        command: "append_asset",
        empty_name: emptyName,
        filepath: asset.filepath,
        asset_name: asset.name,
      });

      // Update local state optimistically (will be reverted if operation fails)
      updatePlacedAssetState(assetId, emptyName);
      toast.info(`Placing ${asset.name} at ${emptyName}`);
    },
    [availableAssets, sendMessage, updatePlacedAssetState]
  );

  const removeAsset = useCallback(
    (assetId: string) => {
      const emptyName = getEmptyNameForAsset(assetId);
      if (!emptyName) {
        toast.error("Asset placement not found");
        return;
      }

      sendMessage({
        command: "remove_assets",
        empty_name: emptyName,
      });

      // Update local state optimistically
      removePlacedAssetState(assetId);
      toast.info(`Removing asset from ${emptyName}`);
    },
    [getEmptyNameForAsset, sendMessage, removePlacedAssetState]
  );

  const rotateAsset = useCallback(
    (assetId: string, degrees: number) => {
      const emptyName = getEmptyNameForAsset(assetId);
      if (!emptyName) {
        toast.error("Asset placement not found");
        return;
      }

      sendMessage({
        command: "rotate_assets",
        empty_name: emptyName,
        degrees,
      });

      // Update local state
      updatePlacedAssetProperties(assetId, { rotation: degrees });
    },
    [getEmptyNameForAsset, sendMessage, updatePlacedAssetProperties]
  );

  const scaleAsset = useCallback(
    (assetId: string, scalePercent: number) => {
      const emptyName = getEmptyNameForAsset(assetId);
      if (!emptyName) {
        toast.error("Asset placement not found");
        return;
      }

      sendMessage({
        command: "scale_assets",
        empty_name: emptyName,
        scale_percent: scalePercent,
      });

      // Update local state
      updatePlacedAssetProperties(assetId, { scale: scalePercent });
    },
    [getEmptyNameForAsset, sendMessage, updatePlacedAssetProperties]
  );

  return {
    placeAsset,
    removeAsset,
    rotateAsset,
    scaleAsset,
  };
}
