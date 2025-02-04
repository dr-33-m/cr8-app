import { LoaderPinwheel, Save } from "lucide-react";
import { Button } from "../ui/button";
import { useFormContext } from "react-hook-form";
import { useMoodboardStore } from "@/store/moodboardStore";
import { MoodboardFormData } from "@/lib/types/moodboard";
import { toast } from "sonner";
import { useState } from "react";

export function MoodboardActions({ moodboardId }) {
  const c8_engine_server = import.meta.env.VITE_CR8_ENGINE_SERVER;
  const {
    formState: { isValid },
    handleSubmit,
    reset,
  } = useFormContext<MoodboardFormData>();

  const resetMoodboard = useMoodboardStore((state) => state.resetMoodboard);
  const [isLoading, setIsLoading] = useState(false);

  const onSubmit = async (data: MoodboardFormData) => {
    try {
      setIsLoading(true);
      const formData = new FormData();

      // Prepare moodboard_data object to match backend expectations
      const moodboardData = {
        storyline: data.storyline,
        keywords: data.keywords,
        industry: data.industry,
        targetAudience: data.targetAudience,
        theme: data.theme,
        tone: data.tone,
        videoReferences: data.videoReferences,
        colorPalette: data.colorPalette,
        usage_intent: data.usageIntent,
        images_metadata: [] as Array<{
          filename: string;
          category: string;
          annotation: string;
        }>,
      };

      // Handle images from different categories
      Object.entries(data.categoryImages).forEach(([category, images]) => {
        images.forEach((image) => {
          moodboardData.images_metadata.push({
            filename: image.file.name,
            category: category,
            annotation: image.annotation || "",
          });

          formData.append("images", image.file);
        });
      });

      // Add the moodboard data as a JSON string
      formData.append("moodboard_data", JSON.stringify(moodboardData));

      const response = await fetch(
        `${c8_engine_server}/api/v1/moodboards/update_moodboard/${moodboardId}`,
        {
          method: "PUT",
          body: formData,
        }
      );

      if (!response.ok) {
        toast.error("Failed to save moodboard");
        throw new Error("Failed to save moodboard");
      }

      if (response.ok) {
        toast.success("Moodboard saved successfully");
        const defaultValues = {
          categoryImages: {
            compositions: [],
            actions: [],
            lighting: [],
            location: [],
          },
          colorPalette: [],
          videoReferences: [],
          keywords: [],
          theme: undefined,
          tone: undefined,
          industry: undefined,
          targetAudience: "",
          usageIntent: undefined,
          storyline: "",
        };

        reset(defaultValues);
        resetMoodboard();
      }

      return await response.json();
    } catch (error) {
      toast.error("Error saving moodboard:", error);
      console.error("Error saving moodboard:", error);
      throw error;
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Button
      variant="ghost"
      size="default"
      title="Save Moodboard"
      disabled={!isValid || isLoading}
      className="hover:bg-white/10"
      type="button"
      onClick={handleSubmit(onSubmit)}
    >
      {isLoading ? (
        <LoaderPinwheel className="h-5 w-5 animate-spin" />
      ) : (
        <Save className="h-5 w-5" />
      )}
      <span>{isLoading ? "Saving Moodboard..." : "Save Moodboard"}</span>
    </Button>
  );
}
