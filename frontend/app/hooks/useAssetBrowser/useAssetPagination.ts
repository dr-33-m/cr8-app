import { useState } from "react";
import { PaginationOptions } from "@/lib/types/assetBrowser";

export function useAssetPagination(options: PaginationOptions = {}) {
  const { initialPage = 1, initialLimit = 20 } = options;

  const [page, setPage] = useState(initialPage);
  const [limit, setLimit] = useState(initialLimit);

  const setLimitAndResetPage = (newLimit: number) => {
    setLimit(newLimit);
    setPage(1); // Reset to page 1 when limit changes
  };

  const reset = () => {
    setPage(initialPage);
    setLimit(initialLimit);
  };

  return {
    page,
    limit,
    setPage,
    setLimit: setLimitAndResetPage,
    nextPage: () => setPage((prev) => prev + 1),
    prevPage: () => setPage((prev) => Math.max(1, prev - 1)),
    firstPage: () => setPage(1),
    lastPage: (totalPages: number) => setPage(totalPages),
    reset,
  };
}
