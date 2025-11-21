# Server Architecture Pattern

This document outlines the standardized pattern for implementing server-related functionality in the cr8-app frontend. This pattern ensures consistent data fetching, caching, and state management across all server interactions.

## Overview

The server architecture follows a **query-manager + hooks approach** with three main layers:

1. **Server Functions** - TanStack React Start server functions with validation
2. **Query Manager** - React Query configuration with keys and options
3. **Hooks** - Consumer hooks that handle data fetching and state management

## Directory Structure

```
frontend/app/server/
├── api/
│   ├── validations/
│   │   └── [service]/
│   │       └── [service].ts          # Zod validation schemas
│   └── [service]/
│       ├── [function].ts             # Individual server functions
│       └── index.ts                  # Barrel export of functions
└── query-manager/
    └── [service]/
        ├── keys.ts                   # Query key factory
        ├── options.ts                # Query option creators
        └── index.ts                  # Barrel export
```

## 1. Server Functions Layer

### Validation Schemas

Create Zod schemas in `frontend/app/server/api/validations/[service]/[service].ts`:

```typescript
import { z } from "zod";

export const AssetTypeSchema = z.enum(["hdris", "textures", "models"]);

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
```

### Server Functions

Create individual server functions in `frontend/app/server/api/[service]/[function].ts`:

```typescript
import { createServerFn } from "@tanstack/react-start";
import { GetAssetsPaginatedSchema } from "../validations/[service]";
import type { PaginatedAssetsResponse } from "@/lib/types/[service]";

export const getAssetsPaginatedFn = createServerFn({ method: "GET" })
  .inputValidator(GetAssetsPaginatedSchema)
  .handler(async ({ data }): Promise<PaginatedAssetsResponse> => {
    const baseUrl = process.env.API_URL || "http://localhost:8000";

    const params = new URLSearchParams();
    // Build query parameters...

    const response = await fetch(
      `${baseUrl}/api/v1/[service]/[endpoint]?${params.toString()}`,
      {
        method: "GET",
        headers: { "Content-Type": "application/json" },
      }
    );

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({
        detail: "Unknown error occurred",
      }));
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    return response.json();
  });
```

### Server Functions Index

Create barrel export in `frontend/app/server/api/[service]/index.ts`:

```typescript
export { getAssetsPaginatedFn } from "./getAssetsPaginated";
export { getAssetInfoFn } from "./getAssetInfo";
// ... other exports
```

## 2. Query Manager Layer

### Query Keys

Create key factory in `frontend/app/server/query-manager/[service]/keys.ts`:

```typescript
export const [service]Keys = {
  all: ["[service]"] as const,

  [resource]: (params: ParamsType) =>
    [...[service]Keys.all, "[resource]", params] as const,

  [resource]ById: (id: string) =>
    [...[service]Keys.all, "[resource]", id] as const,
};
```

### Query Options

Create option creators in `frontend/app/server/query-manager/[service]/options.ts`:

```typescript
import { UseQueryOptions } from "@tanstack/react-query";
import { [function]Fn } from "@/server/api/[service]";
import type { ReturnType } from "@/lib/types/[service]";
import { [service]Keys } from "./keys";

export function create[Resource]QueryOptions<
  TData = ReturnType,
  TError = Error
>(
  params: ParamsType,
  options?: Omit<
    UseQueryOptions<ReturnType, TError, TData>,
    "queryKey" | "queryFn"
  >
) {
  return {
    staleTime: [appropriate_time], // Based on data freshness needs
    gcTime: [appropriate_time],     // Based on cache retention needs
    ...options,
    queryKey: [service]Keys.[resource](params),
    queryFn: () => [function]Fn({ data: params }),
  } satisfies UseQueryOptions<ReturnType, TError, TData>;
}
```

### Query Manager Index

Create barrel export in `frontend/app/server/query-manager/[service]/index.ts`:

```typescript
export { [service]Keys } from "./keys";
export {
  create[Resource]QueryOptions,
  // ... other exports
} from "./options";
```

## 3. Hooks Layer

### Data Fetching Hooks

Refactor existing hooks to use React Query instead of manual state management:

```typescript
import { useQuery } from "@tanstack/react-query";
import { create[Resource]QueryOptions } from "@/server/query-manager/[service]";

export function use[Resource](params: ParamsType) {
  const { data, isLoading, error, refetch } = useQuery(
    create[Resource]QueryOptions(params)
  );

  // Transform data to match existing interface if needed
  const transformedData = data ? transformData(data) : [];

  return {
    data: transformedData,
    loading: isLoading,
    error: error?.message,
    refresh: refetch,
  };
}
```

### State Management Separation

**Server State (React Query):**

- Data fetching and caching
- Loading and error states
- Automatic refetching

**UI State (useState/useReducer):**

- User selections and filters
- Form inputs
- Component-specific state

## Caching Strategy Guidelines

### staleTime (How long data stays fresh)

- **Static data**: 30 minutes - 1 hour (asset info, author details)
- **Moderately changing**: 5-15 minutes (categories, asset lists)
- **Dynamic data**: 1-2 minutes (paginated results, search)
- **Real-time data**: 30 seconds (health checks, status)

### gcTime (How long to keep in cache)

- **Frequently accessed**: 2x staleTime (keep longer for performance)
- **Rarely accessed**: 1x staleTime (don't waste memory)
- **Large data**: Shorter gcTime (free memory sooner)

## Implementation Workflow

1. **Create validation schemas** - Define input/output types
2. **Implement server functions** - Add API calls with error handling
3. **Build query manager** - Keys and options with appropriate caching
4. **Refactor hooks** - Replace manual state with React Query
5. **Update components** - Ensure backward compatibility

## Benefits

- **Consistent API** - Standardized pattern across all server interactions
- **Automatic caching** - React Query handles cache invalidation and background updates
- **Type safety** - Full TypeScript support with proper inference
- **Performance** - Intelligent caching reduces unnecessary requests
- **Maintainability** - Clear separation of concerns and predictable structure

## Example: Complete Implementation

See the Polyhaven implementation in this chat for a complete working example:

- `frontend/app/server/api/polyhaven/` - Server functions
- `frontend/app/server/query-manager/polyhaven/` - Query configuration
- `frontend/app/hooks/useAssetBrowser/` - Refactored hooks
