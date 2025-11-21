export const polyhavenKeys = {
  all: ["polyhaven"] as const,

  assetTypes: () => [...polyhavenKeys.all, "assetTypes"] as const,

  assets: (params: {
    assetType?: string;
    categories?: string[];
    page?: number;
    limit?: number;
    search?: string;
  }) => [...polyhavenKeys.all, "assets", params] as const,

  assetInfo: (assetId: string) =>
    [...polyhavenKeys.all, "assetInfo", assetId] as const,

  assetFiles: (assetId: string) =>
    [...polyhavenKeys.all, "assetFiles", assetId] as const,

  categories: (assetType: string, inCategories?: string[]) =>
    [...polyhavenKeys.all, "categories", assetType, { inCategories }] as const,

  authorInfo: (authorId: string) =>
    [...polyhavenKeys.all, "authorInfo", authorId] as const,

  health: () => [...polyhavenKeys.all, "health"] as const,
};
