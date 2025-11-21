import {
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
} from "@/components/ui/pagination";
import { MAX_VISIBLE_PAGES } from "./dialogs/AssetDialogView";

export function PaginationPages({
  currentPage,
  totalPages,
  loading,
  onPageClick,
}: {
  currentPage: number;
  totalPages: number;
  loading: boolean;
  onPageClick: (page: number) => void;
}) {
  const startPage = Math.max(1, currentPage - 2);
  const visiblePages = Math.min(MAX_VISIBLE_PAGES, totalPages);
  const showEllipsis =
    totalPages > MAX_VISIBLE_PAGES && currentPage < totalPages - 2;

  return (
    <>
      {Array.from({ length: visiblePages }, (_, i) => {
        const pageNum = startPage + i;
        if (pageNum > totalPages) return null;

        return (
          <PaginationItem key={pageNum}>
            <PaginationLink
              size="icon"
              onClick={() => onPageClick(pageNum)}
              isActive={pageNum === currentPage}
              className={loading ? "pointer-events-none opacity-50" : ""}
            >
              {pageNum}
            </PaginationLink>
          </PaginationItem>
        );
      })}

      {showEllipsis && (
        <>
          <PaginationItem>
            <PaginationEllipsis />
          </PaginationItem>
          <PaginationItem>
            <PaginationLink
              size="icon"
              onClick={() => onPageClick(totalPages)}
              className={loading ? "pointer-events-none opacity-50" : ""}
            >
              {totalPages}
            </PaginationLink>
          </PaginationItem>
        </>
      )}
    </>
  );
}
