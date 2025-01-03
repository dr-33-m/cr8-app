import { Upload, Info } from "lucide-react";
import { Button } from "@/components/ui/button";
import { ImageWithAnnotation } from "@/types/moodboard";
import { ImageCarousel } from "./ImageCarousel";
import { ChangeEvent } from "react";
import { FormError } from "@/components/ui/form-error";
import { useFormContext } from "react-hook-form";

interface ImageSectionProps {
  title: string;
  description: string;
  images: ImageWithAnnotation[];
  onImagesChange: (images: ImageWithAnnotation[]) => void;
  category: string;
  maxImages?: number;
}

export function ImageSection({
  title,
  description,
  images,
  onImagesChange,
  category,
  maxImages = 5,
}: ImageSectionProps) {
  const {
    formState: { errors },
  } = useFormContext();
  const error = errors.categoryImages?.[category]?.message;

  const handleImageUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    const newImages = files.map((file) => ({ file, annotation: "" }));
    onImagesChange([...images, ...newImages].slice(0, maxImages));
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
    <div className="space-y-3 p-4 rounded-lg bg-cr8-dark/30 border border-cr8-charcoal/50 backdrop-blur-md">
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="space-y-1">
            <h3 className="text-sm font-medium text-white">{title}</h3>
            <div className="flex items-center gap-2 text-xs text-white/60">
              <Info className="h-3 w-3" />
              <p>{description}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-white/60">
              {images.length}/{maxImages} images
            </span>
            <label>
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleImageUpload}
                className="hidden"
                disabled={images.length >= maxImages}
              />
              <Button
                variant="glass"
                size="sm"
                asChild
                disabled={images.length >= maxImages}
              >
                <span>
                  <Upload className="mr-2 h-4 w-4" />
                  Upload
                </span>
              </Button>
            </label>
          </div>
        </div>
      </div>

      {images.length > 0 ? (
        <ImageCarousel
          images={images}
          onAnnotationChange={handleAnnotationChange}
          onRemove={removeImage}
        />
      ) : (
        <div className="flex items-center justify-center h-32 rounded-lg border-2 border-dashed border-cr8-charcoal/50 bg-cr8-dark/20">
          <p className="text-sm text-white/60">Upload images to get started</p>
        </div>
      )}

      <FormError message={error as string} />
    </div>
  );
}
