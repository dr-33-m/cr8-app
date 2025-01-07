import { BaseNode } from "./BaseNode";
import { ImageSection } from "./visual/ImageSection";
import { ColorPalette } from "./visual/ColorPalette";
import { VideoReferences } from "./visual/VideoReference";
import {
  CategoryImages,
  ImageWithAnnotation,
  MoodboardFormData,
} from "@/types/moodboard";
import { useFormContext } from "react-hook-form";
import { FormError } from "@/components/ui/form-error";

type CategoryKeys = keyof CategoryImages;

export function VisualNode() {
  const {
    formState: { errors },
    setValue,
    watch,
  } = useFormContext<MoodboardFormData>();

  const categoryImages = watch("categoryImages");
  const colorPalette = watch("colorPalette") || [];
  const videoReferences = watch("videoReferences") || [];

  const updateImages = (
    category: CategoryKeys,
    newImages: ImageWithAnnotation[]
  ) => {
    setValue(`categoryImages.${category}`, newImages, {
      shouldValidate: true,
    });
  };
  return (
    <BaseNode
      title="Visual Elements"
      showSourceHandle
      titleColor="text-cr8-blue"
    >
      <div className="space-y-6">
        <div className="grid grid-cols-2 gap-4">
          <ImageSection
            title="Compositions"
            description="Reference images for camera angles and framing"
            images={
              (categoryImages?.compositions || []) as ImageWithAnnotation[]
            }
            onImagesChange={(images) => updateImages("compositions", images)}
            category="compositions"
          />

          <ImageSection
            title="Actions & Activities"
            description="Reference images for poses and interactions"
            images={(categoryImages?.actions || []) as ImageWithAnnotation[]}
            onImagesChange={(images) => updateImages("actions", images)}
            category="actions"
          />

          <ImageSection
            title="Lighting"
            description="Reference images for lighting setup and mood"
            images={(categoryImages?.lighting || []) as ImageWithAnnotation[]}
            onImagesChange={(images) => updateImages("lighting", images)}
            category="lighting"
          />

          <ImageSection
            title="Location"
            description="Reference images for scene and environment"
            images={(categoryImages?.location || []) as ImageWithAnnotation[]}
            onImagesChange={(images) => updateImages("location", images)}
            category="location"
          />
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="p-4 rounded-lg bg-cr8-dark/30 border border-cr8-charcoal/50 backdrop-blur-md">
            <ColorPalette
              colors={colorPalette}
              onColorsChange={(colors) =>
                setValue("colorPalette", colors, {
                  shouldValidate: true,
                })
              }
            />
            <FormError message={errors.colorPalette?.message as string} />
          </div>

          <div className="p-4 rounded-lg bg-cr8-dark/30 border border-cr8-charcoal/50 backdrop-blur-md">
            <VideoReferences
              videos={videoReferences}
              onVideosChange={(videos) =>
                setValue("videoReferences", videos, {
                  shouldValidate: true,
                })
              }
            />
            <FormError message={errors.videoReferences?.message as string} />
          </div>
        </div>
      </div>
    </BaseNode>
  );
}
