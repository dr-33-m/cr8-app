export interface Asset {
  id: string;
  name: string;
  filepath: string;
  thumbnailUrl?: string;
}

export interface PlacedAsset {
  assetId: string;
  emptyName: string;
  rotation?: number;
  scale?: number;
}

export interface AssetPlacerState {
  availableAssets: Asset[];
  placedAssets: PlacedAsset[];
  selectedAssetId: string | null;

  // Actions
  setAvailableAssets: (assets: Asset[]) => void;
  selectAsset: (id: string | null) => void;
  placeAsset: (assetId: string, emptyName: string) => void;
  removePlacedAsset: (assetId: string) => void;
  updatePlacedAsset: (
    assetId: string,
    updates: Partial<Omit<PlacedAsset, "assetId">>
  ) => void;
  isAssetPlaced: (assetId: string) => boolean;
  getPlacedAssetByEmptyName: (emptyName: string) => PlacedAsset | undefined;
  getEmptyNameForAsset: (assetId: string) => string | undefined;
  clearPlacedAssets: () => void;
}

// Initial static assets (to be replaced with API call later)
export const STATIC_ASSETS: Asset[] = [
  {
    id: "asset1",
    name: "Jordan 1s Blue L",
    filepath:
      "/home/thamsanqa/Cr8-xyz Creative Studio/Templates/Shoes/street_wear_shoes.blend",
    thumbnailUrl:
      "https://s3.amazonaws.com/stockx-sneaker-analysis/wp-content/uploads/2018/01/Air-Jordan-1-Retro-High-Alternate-Black-Royal.png",
  },
  {
    id: "asset2",
    name: "Jordan 1s Black L",
    filepath:
      "/home/thamsanqa/Cr8-xyz Creative Studio/Templates/Shoes/street_wear_shoes.blend",
    thumbnailUrl:
      "https://www.highsnobiety.com/static-assets/dato/1666535321-air-jordan-1-black-white-panda-date-price.jpg",
  },
  {
    id: "asset3",
    name: "AirMags L",
    filepath:
      "/home/thamsanqa/Cr8-xyz Creative Studio/Templates/Shoes/street_wear_shoes.blend",
    thumbnailUrl:
      "https://www.adweek.com/wp-content/uploads/files/blogs/nike-mag-hed-2016.jpg",
  },
  {
    id: "asset4",
    name: "mschf L",
    filepath:
      "/home/thamsanqa/Cr8-xyz Creative Studio/Templates/Shoes/street_wear_shoes.blend",
    thumbnailUrl:
      "https://images.summitmedia-digital.com/preview/images/2023/02/20/andrea-brillantes-mschf-boots---insert.jpg",
  },
  {
    id: "asset5",
    name: "nmds L",
    filepath:
      "/home/thamsanqa/Cr8-xyz Creative Studio/Templates/Shoes/street_wear_shoes.blend",
    thumbnailUrl:
      "https://sneakernews.com/wp-content/uploads/2021/05/adidas-NMD-R1-GZ7922-1.jpg",
  },
];
