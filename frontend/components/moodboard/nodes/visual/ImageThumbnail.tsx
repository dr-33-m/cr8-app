import { X, MessageSquare } from "lucide-react";
import { useState } from "react";

interface ImageThumbnailProps {
  file: File;
  annotation?: string;
  onRemove: () => void;
  onAnnotationChange: (annotation: string) => void;
}

export function ImageThumbnail({
  file,
  annotation,
  onRemove,
  onAnnotationChange,
}: ImageThumbnailProps) {
  const [showAnnotation, setShowAnnotation] = useState(false);

  return (
    <div className="group relative w-32 h-32">
      <div className="relative h-full rounded-lg overflow-hidden border border-charcoal-700/50 bg-charcoal-800/30 backdrop-blur-md">
        <img
          src={URL.createObjectURL(file)}
          alt={`Upload ${file.name}`}
          className="w-full h-full object-cover"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />

        <div className="absolute top-2 right-2 flex gap-2">
          <button
            onClick={() => setShowAnnotation(true)}
            className="p-1 rounded-full bg-charcoal-900/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
            title={annotation || "Add note"}
          >
            <MessageSquare className="h-3 w-3" />
          </button>
          <button
            onClick={onRemove}
            className="p-1 rounded-full bg-charcoal-900/80 text-white opacity-0 group-hover:opacity-100 transition-opacity"
          >
            <X className="h-3 w-3" />
          </button>
        </div>

        {annotation && (
          <div className="absolute bottom-0 left-0 right-0 p-1 bg-charcoal-900/80 text-xs text-white truncate">
            {annotation}
          </div>
        )}
      </div>

      {showAnnotation && (
        <div className="absolute inset-0 z-10 bg-charcoal-900/95 backdrop-blur-sm rounded-lg p-2">
          <textarea
            className="w-full h-full bg-transparent text-white text-xs resize-none border border-charcoal-700/50 rounded p-1"
            placeholder="Add a note about this image..."
            value={annotation}
            onChange={(e) => onAnnotationChange(e.target.value)}
            onBlur={() => setShowAnnotation(false)}
            autoFocus
          />
        </div>
      )}
    </div>
  );
}
