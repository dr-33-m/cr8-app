import { useState, useCallback, useEffect } from "react";

import { SearchState, SearchOptions } from "@/lib/types/assetBrowser";

export function useAssetSearch(options: SearchOptions = {}) {
  const { initialQuery = "", debounceMs = 300 } = options;

  const [state, setState] = useState<SearchState>({
    query: initialQuery,
    debouncedQuery: initialQuery,
  });

  const setQuery = useCallback((query: string) => {
    setState((prev) => ({ ...prev, query }));
  }, []);

  const clearQuery = useCallback(() => {
    setState({ query: "", debouncedQuery: "" });
  }, []);

  // Debounce the query
  useEffect(() => {
    const timer = setTimeout(() => {
      setState((prev) => ({ ...prev, debouncedQuery: prev.query }));
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [state.query, debounceMs]);

  return {
    ...state,
    setQuery,
    clearQuery,
  };
}
