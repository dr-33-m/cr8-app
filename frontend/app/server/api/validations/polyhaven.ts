import { z } from "zod";

export const AssetTypeSchema = z.enum(["hdris", "textures", "models"]);

export const GetAssetTypesSchema = z.object({});

export const GetAssetsSchema = z.object({
  assetType: AssetTypeSchema.optional(),
  categories: z.array(z.string()).optional(),
});

export const GetAssetsPaginatedSchema = z.object({
  assetType: AssetTypeSchema.optional(),
  categories: z.array(z.string()).optional(),
  page: z.number().int().positive().default(1),
  limit: z.number().int().positive().default(20),
  search: z.string().optional(),
});

export const GetAssetInfoSchema = z.object({
  assetId: z.string().min(1),
});

export const GetAssetFilesSchema = z.object({
  assetId: z.string().min(1),
});

export const GetCategoriesSchema = z.object({
  assetType: AssetTypeSchema,
  inCategories: z.array(z.string()).optional(),
});

export const GetAuthorInfoSchema = z.object({
  authorId: z.string().min(1),
});

export const CheckHealthSchema = z.object({});
