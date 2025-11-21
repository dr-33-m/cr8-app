import { UseQueryOptions } from "@tanstack/react-query";
import type { AssetType } from "@/lib/types/assetBrowser";
import {
  getAssetTypesFn,
  getAssetsFn,
  getAssetsPaginatedFn,
  getAssetInfoFn,
  getAssetFilesFn,
  getCategoriesFn,
  getAuthorInfoFn,
  checkHealthFn,
} from "@/server/api/polyhaven";
import type {
  AssetTypesResponse,
  PaginatedAssetsResponse,
  HDRIAsset,
  TextureAsset,
  ModelAsset,
  AssetFiles,
  CategoriesResponse,
  Author,
} from "@/lib/types/assetBrowser";
import { polyhavenKeys } from "./keys";

export function createAssetTypesQueryOptions<
  TData = AssetTypesResponse,
  TError = Error
>(
  options?: Omit<
    UseQueryOptions<AssetTypesResponse, TError, TData>,
    "queryKey" | "queryFn"
  >
) {
  return {
    staleTime: 60 * 60 * 1000, // 1 hour
    gcTime: 24 * 60 * 60 * 1000, // 24 hours
    ...options,
    queryKey: polyhavenKeys.assetTypes(),
    queryFn: () => getAssetTypesFn({ data: {} }),
  } satisfies UseQueryOptions<AssetTypesResponse, TError, TData>;
}

export function createAssetsQueryOptions<
  TData = PaginatedAssetsResponse,
  TError = Error
>(
  params: {
    assetType?: AssetType;
    categories?: string[];
  },
  options?: Omit<
    UseQueryOptions<PaginatedAssetsResponse, TError, TData>,
    "queryKey" | "queryFn"
  >
) {
  return {
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    ...options,
    queryKey: polyhavenKeys.assets(params),
    queryFn: () => getAssetsFn({ data: params }),
  } satisfies UseQueryOptions<PaginatedAssetsResponse, TError, TData>;
}

export function createAssetsPaginatedQueryOptions<
  TData = PaginatedAssetsResponse,
  TError = Error
>(
  params: {
    assetType?: AssetType;
    categories?: string[];
    page?: number;
    limit?: number;
    search?: string;
  },
  options?: Omit<
    UseQueryOptions<PaginatedAssetsResponse, TError, TData>,
    "queryKey" | "queryFn"
  >
) {
  return {
    staleTime: 2 * 60 * 1000, // 2 minutes - users might navigate back
    gcTime: 5 * 60 * 1000, // 5 minutes - keep recent pages cached
    ...options,
    queryKey: polyhavenKeys.assets(params),
    queryFn: () =>
      getAssetsPaginatedFn({
        data: {
          assetType: params.assetType,
          categories: params.categories,
          page: params.page ?? 1,
          limit: params.limit ?? 20,
          search: params.search,
        },
      }),
  } satisfies UseQueryOptions<PaginatedAssetsResponse, TError, TData>;
}

export function createAssetInfoQueryOptions<
  TData = HDRIAsset | TextureAsset | ModelAsset,
  TError = Error
>(
  assetId: string,
  options?: Omit<
    UseQueryOptions<HDRIAsset | TextureAsset | ModelAsset, TError, TData>,
    "queryKey" | "queryFn"
  >
) {
  return {
    staleTime: 30 * 60 * 1000, // 30 minutes - asset details are relatively static
    gcTime: 60 * 60 * 1000, // 1 hour - keep viewed assets cached longer
    ...options,
    queryKey: polyhavenKeys.assetInfo(assetId),
    queryFn: () => getAssetInfoFn({ data: { assetId } }),
  } satisfies UseQueryOptions<
    HDRIAsset | TextureAsset | ModelAsset,
    TError,
    TData
  >;
}

export function createAssetFilesQueryOptions<
  TData = AssetFiles,
  TError = Error
>(
  assetId: string,
  options?: Omit<
    UseQueryOptions<AssetFiles, TError, TData>,
    "queryKey" | "queryFn"
  >
) {
  return {
    staleTime: 60 * 60 * 1000, // 1 hour - file lists don't change
    gcTime: 2 * 60 * 60 * 1000, // 2 hours - keep for re-downloads
    ...options,
    queryKey: polyhavenKeys.assetFiles(assetId),
    queryFn: () => getAssetFilesFn({ data: { assetId } }),
  } satisfies UseQueryOptions<AssetFiles, TError, TData>;
}

export function createCategoriesQueryOptions<
  TData = CategoriesResponse,
  TError = Error
>(
  assetType: AssetType,
  inCategories?: string[],
  options?: Omit<
    UseQueryOptions<CategoriesResponse, TError, TData>,
    "queryKey" | "queryFn"
  >
) {
  return {
    staleTime: 15 * 60 * 1000, // 15 minutes
    gcTime: 30 * 60 * 1000, // 30 minutes
    ...options,
    queryKey: polyhavenKeys.categories(assetType, inCategories),
    queryFn: () => getCategoriesFn({ data: { assetType, inCategories } }),
  } satisfies UseQueryOptions<CategoriesResponse, TError, TData>;
}

export function createAuthorInfoQueryOptions<TData = Author, TError = Error>(
  authorId: string,
  options?: Omit<UseQueryOptions<Author, TError, TData>, "queryKey" | "queryFn">
) {
  return {
    staleTime: 30 * 60 * 1000, // 30 minutes
    gcTime: 60 * 60 * 1000, // 1 hour
    ...options,
    queryKey: polyhavenKeys.authorInfo(authorId),
    queryFn: () => getAuthorInfoFn({ data: { authorId } }),
  } satisfies UseQueryOptions<Author, TError, TData>;
}

export function createHealthCheckQueryOptions<
  TData = {
    status: string;
    message: string;
    available_types?: string[];
  },
  TError = Error
>(
  options?: Omit<
    UseQueryOptions<
      {
        status: string;
        message: string;
        available_types?: string[];
      },
      TError,
      TData
    >,
    "queryKey" | "queryFn"
  >
) {
  return {
    staleTime: 30 * 1000, // 30 seconds - health should be recent
    gcTime: 60 * 1000, // 1 minute - don't keep old health checks
    ...options,
    queryKey: polyhavenKeys.health(),
    queryFn: () => checkHealthFn({ data: {} }),
  } satisfies UseQueryOptions<
    {
      status: string;
      message: string;
      available_types?: string[];
    },
    TError,
    TData
  >;
}
