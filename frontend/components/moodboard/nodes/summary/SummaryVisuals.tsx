import { ImageWithAnnotation } from "@/types/moodboard";

interface SummaryVisualsProps {
  images: ImageWithAnnotation[];
  colorPalette: string[];
}

export function SummaryVisuals({ images, colorPalette }: SummaryVisualsProps) {
  return (
    <div className="space-y-4">
      <h3 className="text-sm font-medium text-white">Visual Elements</h3>

      {images.length > 0 && (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {images.slice(0, 3).map((image, index) => (
            <div key={index} className="relative w-20 h-20 flex-shrink-0">
              <img
                src={URL.createObjectURL(image.file)}
                alt={image.annotation || `Image ${index + 1}`}
                className="w-full h-full object-cover rounded-md"
              />
              {image.annotation && (
                <div className="absolute bottom-0 left-0 right-0 p-1 bg-charcoal-900/80 text-[10px] text-white truncate rounded-b-md">
                  {image.annotation}
                </div>
              )}
            </div>
          ))}
          {images.length > 3 && (
            <div className="w-20 h-20 flex-shrink-0 flex items-center justify-center bg-charcoal-800/30 rounded-md text-sm text-white">
              +{images.length - 3} more
            </div>
          )}
        </div>
      )}

      {colorPalette.length > 0 && (
        <div className="flex gap-2">
          {colorPalette.map((color, index) => (
            <div
              key={index}
              className="w-6 h-6 rounded-full border border-charcoal-700/50"
              style={{ backgroundColor: color }}
              title={color}
            />
          ))}
        </div>
      )}
    </div>
  );
}
