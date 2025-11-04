import { useState, useCallback } from "react";

export interface PaginationState {
  page: number;
  limit: number;
  totalPages: number;
  totalCount: number;
  hasNext: boolean;
  hasPrev: boolean;
}

export interface PaginationOptions {
  initialPage?: number;
  initialLimit?: number;
}

export function useAssetPagination(options: PaginationOptions = {}) {
  const { initialPage = 1, initialLimit = 20 } = options;

  const [state, setState] = useState<PaginationState>({
    page: initialPage,
    limit: initialLimit,
    totalPages: 0,
    totalCount: 0,
    hasNext: false,
    hasPrev: false,
  });

  const setPage = useCallback((page: number) => {
    setState((prev) => ({ ...prev, page }));
  }, []);

  const setLimit = useCallback((limit: number) => {
    setState((prev) => ({ ...prev, limit, page: 1 })); // Reset to page 1 when limit changes
  }, []);

  const nextPage = useCallback(() => {
    setState((prev) =>
      prev.hasNext ? { ...prev, page: prev.page + 1 } : prev
    );
  }, []);

  const prevPage = useCallback(() => {
    setState((prev) =>
      prev.hasPrev ? { ...prev, page: prev.page - 1 } : prev
    );
  }, []);

  const firstPage = useCallback(() => {
    setState((prev) => ({ ...prev, page: 1 }));
  }, []);

  const lastPage = useCallback(() => {
    setState((prev) => ({ ...prev, page: prev.totalPages }));
  }, []);

  const updatePagination = useCallback(
    (pagination: {
      page: number;
      limit: number;
      total_count: number;
      total_pages: number;
      has_next: boolean;
      has_prev: boolean;
    }) => {
      setState((prev) => ({
        ...prev,
        page: pagination.page,
        limit: pagination.limit,
        totalPages: pagination.total_pages,
        totalCount: pagination.total_count,
        hasNext: pagination.has_next,
        hasPrev: pagination.has_prev,
      }));
    },
    []
  );

  const reset = useCallback(() => {
    setState({
      page: initialPage,
      limit: initialLimit,
      totalPages: 0,
      totalCount: 0,
      hasNext: false,
      hasPrev: false,
    });
  }, [initialPage, initialLimit]);

  return {
    ...state,
    setPage,
    setLimit,
    nextPage,
    prevPage,
    firstPage,
    lastPage,
    updatePagination,
    reset,
  };
}
