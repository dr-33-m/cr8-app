import { useState, useEffect } from "react";
import { SearchOptions } from "@/lib/types/assetBrowser";

export function useAssetSearch(options: SearchOptions = {}) {
  const { initialQuery = "", debounceMs = 300 } = options;

  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);

  const clearQuery = () => {
    setQuery("");
    setDebouncedQuery("");
  };

  // Debounce the query
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedQuery(query);
    }, debounceMs);

    return () => clearTimeout(timer);
  }, [query, debounceMs]);

  return {
    query,
    debouncedQuery,
    setQuery,
    clearQuery,
  };
}
