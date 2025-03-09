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

  const replaceAsset = useCallback(
    (currentAssetId: string, newAssetId: string) => {
      const emptyName = getEmptyNameForAsset(currentAssetId);
      if (!emptyName) {
        toast.error("Asset placement not found");
        return;
      }

      const newAsset = availableAssets.find((a) => a.id === newAssetId);
      if (!newAsset) {
        toast.error("Replacement asset not found");
        return;
      }

      sendMessage({
        command: "append_asset",
        empty_name: emptyName,
        filepath: newAsset.filepath,
        asset_name: newAsset.name,
        mode: "REPLACE",
      });

      // Update local state optimistically
      removePlacedAssetState(currentAssetId);
      updatePlacedAssetState(newAssetId, emptyName);
      toast.info(`Replacing with ${newAsset.name} at ${emptyName}`);
    },
    [
      availableAssets,
      sendMessage,
      getEmptyNameForAsset,
      removePlacedAssetState,
      updatePlacedAssetState,
    ]
  );

  const swapAssets = useCallback(
    (assetId1: string, assetId2: string) => {
      const emptyName1 = getEmptyNameForAsset(assetId1);
      const emptyName2 = getEmptyNameForAsset(assetId2);

      if (!emptyName1 || !emptyName2) {
        toast.error("One or both asset placements not found");
        return;
      }

      sendMessage({
        command: "swap_assets",
        empty1_name: emptyName1,
        empty2_name: emptyName2,
      });

      // Update local state optimistically
      const asset1 = { ...placedAssets.find((a) => a.assetId === assetId1)! };
      const asset2 = { ...placedAssets.find((a) => a.assetId === assetId2)! };

      updatePlacedAssetProperties(assetId1, { emptyName: emptyName2 });
      updatePlacedAssetProperties(assetId2, { emptyName: emptyName1 });

      toast.info(`Swapping assets between ${emptyName1} and ${emptyName2}`);
    },
    [
      sendMessage,
      getEmptyNameForAsset,
      placedAssets,
      updatePlacedAssetProperties,
    ]
  );

  return {
    placeAsset,
    removeAsset,
    rotateAsset,
    scaleAsset,
    replaceAsset,
    swapAssets,
  };
}
