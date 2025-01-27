import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ImageThumbnail } from "./ImageThumbnail";
import { ImageWithAnnotation } from "@/lib/types/moodboard";
import { ChangeEvent } from "react";

interface ImageGalleryProps {
  images: ImageWithAnnotation[];
  onImagesChange: (images: ImageWithAnnotation[]) => void;
}

export function ImageGallery({ images, onImagesChange }: ImageGalleryProps) {
  const handleImageUpload = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const newImages = files.map((file) => ({ file, annotation: "" }));
    onImagesChange([...images, ...newImages].slice(0, 10));
  };

  const handleAnnotationChange = (index: number, annotation: string) => {
    const updatedImages = images.map((img, i) =>
      i === index ? { ...img, annotation } : img
    );
    onImagesChange(updatedImages);
  };

  const removeImage = (index: number) => {
    onImagesChange(images.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium text-white">
          Images ({images.length}/10)
        </h3>
        <label>
          <input
            type="file"
            multiple
            accept="image/*"
            onChange={handleImageUpload}
            className="hidden"
          />
          <Button variant="glass" size="sm" asChild>
            <span>
              <Upload className="mr-2 h-4 w-4" />
              Upload
            </span>
          </Button>
        </label>
      </div>

      <div className="grid grid-cols-2 gap-3 max-h-[280px] overflow-y-auto p-2">
        {images.map((image, index) => (
          <ImageThumbnail
            key={index}
            file={image.file}
            annotation={image.annotation}
            onRemove={() => removeImage(index)}
            onAnnotationChange={(annotation) =>
              handleAnnotationChange(index, annotation)
            }
          />
        ))}
      </div>
    </div>
  );
}
