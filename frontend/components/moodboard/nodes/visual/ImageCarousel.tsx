import { ChevronLeft, ChevronRight, MessageSquare } from "lucide-react";
import { ImageWithAnnotation } from "@/lib/types/moodboard";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useEffect, useState } from "react";

interface ImageCarouselProps {
  images: ImageWithAnnotation[];
  onAnnotationChange: (index: number, annotation: string) => void;
  onRemove: (index: number) => void;
}

export function ImageCarousel({
  images,
  onAnnotationChange,
  onRemove,
}: ImageCarouselProps) {
  const [currentPage, setCurrentPage] = useState(0);
  const [editingAnnotation, setEditingAnnotation] = useState<number | null>(
    null
  );

  const imagesPerPage = 4;
  const totalPages = Math.ceil(images.length / imagesPerPage);

  useEffect(() => {
    const maxValidPage = Math.max(0, totalPages - 1);
    if (currentPage > maxValidPage) {
      setCurrentPage(maxValidPage);
    }
  }, [images.length, totalPages, currentPage]);

  const nextPage = () => setCurrentPage((p) => (p + 1) % totalPages);
  const prevPage = () =>
    setCurrentPage((p) => (p - 1 + totalPages) % totalPages);

  const currentImages = images.slice(
    currentPage * imagesPerPage,
    (currentPage + 1) * imagesPerPage
  );

  if (images.length === 0) return null;

  return (
    <div className="relative group">
      <div className="grid grid-cols-2 gap-1">
        {currentImages.map((image, idx) => {
          const imageIndex = currentPage * imagesPerPage + idx;
          return (
            <div key={imageIndex} className="relative aspect-square group">
              <div className="relative h-32 w-32 rounded-lg overflow-hidden border border-charcoal-700/50 bg-charcoal-800/30">
                <img
                  src={URL.createObjectURL(image.file)}
                  alt={image.annotation || `Image ${imageIndex + 1}`}
                  className="h-32 w-32 object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

                <div className="absolute top-2 right-2 flex gap-2">
                  <button
                    onClick={() => setEditingAnnotation(imageIndex)}
                    className="p-1.5 rounded-full bg-charcoal-900/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    <MessageSquare className="h-3.5 w-3.5" />
                  </button>
                  <button
                    onClick={() => onRemove(imageIndex)}
                    className="p-1.5 rounded-full bg-charcoal-900/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
                  >
                    ×
                  </button>
                </div>

                {image.annotation && (
                  <div className="absolute bottom-0 left-0 right-0 p-2 bg-gradient-to-t from-black/60 to-transparent">
                    <p className="text-xs text-white truncate">
                      {image.annotation}
                    </p>
                  </div>
                )}
              </div>

              {editingAnnotation === imageIndex && (
                <div className="absolute inset-0 z-10 bg-charcoal-900/95 backdrop-blur-sm rounded-lg p-2">
                  <textarea
                    className="w-full h-full bg-transparent text-white text-xs resize-none border border-charcoal-700/50 rounded p-1"
                    placeholder="Add a note about this image..."
                    value={image.annotation}
                    onChange={(e) =>
                      onAnnotationChange(imageIndex, e.target.value)
                    }
                    onBlur={() => setEditingAnnotation(null)}
                    autoFocus
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>

      {images.length > imagesPerPage && (
        <>
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "absolute -left-3 top-1/2 -translate-y-1/2",
              "opacity-0 group-hover:opacity-100 transition-opacity"
            )}
            onClick={prevPage}
            disabled={currentPage === 0}
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "absolute -right-3 top-1/2 -translate-y-1/2",
              "opacity-0 group-hover:opacity-100 transition-opacity"
            )}
            onClick={nextPage}
            disabled={currentPage === totalPages - 1}
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
          <div className="absolute -bottom-4 left-1/2 -translate-x-1/2 flex gap-1">
            {Array.from({ length: totalPages }).map((_, index) => (
              <button
                key={index}
                className={cn(
                  "w-1.5 h-1.5 rounded-full transition-colors",
                  index === currentPage ? "bg-white" : "bg-white/30"
                )}
                onClick={() => setCurrentPage(index)}
              />
            ))}
          </div>
        </>
      )}
    </div>
  );
}
