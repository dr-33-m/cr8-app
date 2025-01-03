import { Save } from "lucide-react";
import { Button } from "../ui/button";
import { useFormContext } from "react-hook-form";
import { useMoodboardStore } from "@/store/moodboardStore";
import { MoodboardFormData } from "@/types/moodboard";

export function MoodboardActions() {
  const {
    formState: { isValid },
    handleSubmit,
    reset,
  } = useFormContext<MoodboardFormData>();

  const moodboard = useMoodboardStore((state) => state.moodboard);
  const resetMoodboard = useMoodboardStore((state) => state.resetMoodboard);

  const onSubmit = async (data: MoodboardFormData) => {
    try {
      console.log(moodboard, "moodboard data fom submit btn");
      const formData = new FormData();

      // Handle images
      Object.entries(data.categoryImages).forEach(([category, images]) => {
        images.forEach((image, index) => {
          formData.append(`${category}[${index}]`, image.file);
          formData.append(`${category}Annotations[${index}]`, image.annotation);
        });
      });

      // Add other form data
      Object.entries(data).forEach(([key, value]) => {
        if (key !== "categoryImages") {
          formData.append(
            key,
            typeof value === "object" ? JSON.stringify(value) : value
          );
        }
      });

      const response = await fetch("/api/moodboard", {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("Failed to save moodboard");
      }

      if (response.ok) {
        // Reset both form and store
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
      console.error("Error saving moodboard:", error);
      throw error;
    }
  };

  return (
    <Button
      variant="ghost"
      size="default"
      title="Save Moodboard"
      disabled={!isValid}
      className="hover:bg-white/10"
      type="button"
      onClick={handleSubmit(onSubmit)}
    >
      <Save className="h-5 w-5" />
      <span>Save Moodboard</span>
    </Button>
  );
}
