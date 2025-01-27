import { z } from "zod";

export type Theme =
  | "minimalist"
  | "futuristic"
  | "rustic"
  | "industrial"
  | "vibrant"
  | "custom";
export type Tone =
  | "joyful"
  | "melancholic"
  | "energetic"
  | "serene"
  | "bold"
  | "dreamy";
export type Industry =
  | "fashion"
  | "music"
  | "real-estate"
  | "tech"
  | "entertainment"
  | "custom";
export type UsageIntent =
  | "product-launch"
  | "music-video"
  | "social-media"
  | "commercial";

export interface ImageWithAnnotation {
  file: File;
  annotation?: string;
}

export interface CategoryImages {
  compositions: ImageWithAnnotation[];
  actions: ImageWithAnnotation[];
  lighting: ImageWithAnnotation[];
  location: ImageWithAnnotation[];
}

export interface MoodboardData {
  id: number;
  name: string;
  description: string;
  user_id: number;
  categoryImages: CategoryImages;
  colorPalette: string[];
  videoReferences: string[];
  theme: Theme;
  storyline: string;
  keywords: string[];
  tone: Tone;
  industry: Industry;
  targetAudience: string;
  usageIntent: UsageIntent;
}

// Zod Types

// Define the file schema if not already defined
const fileSchema = z.object({
  file: z.instanceof(File),
  annotation: z.string().optional(),
});

export const moodboardSchema = z.object({
  categoryImages: z.object({
    compositions: z
      .array(fileSchema)
      .min(1, "Add at least one composition reference image"),
    actions: z
      .array(fileSchema)
      .min(1, "Add at least one action reference image"),
    lighting: z
      .array(fileSchema)
      .min(1, "Add at least one lighting reference image"),
    location: z
      .array(fileSchema)
      .min(1, "Add at least one location reference image"),
  }),
  colorPalette: z
    .array(z.string())
    .min(1, "Add at least one color to the palette"),
  videoReferences: z.array(z.string().url("Please enter a valid URL")),
  theme: z.enum(
    [
      "minimalist",
      "futuristic",
      "rustic",
      "industrial",
      "vibrant",
      "custom",
    ] as const,
    {
      required_error: "Please select a theme",
    }
  ),
  storyline: z.string().min(1, "Please enter a storyline"),
  keywords: z.array(z.string()).min(1, "Add at least one keyword"),
  tone: z.enum(
    ["joyful", "melancholic", "energetic", "serene", "bold", "dreamy"] as const,
    {
      required_error: "Please select a tone",
    }
  ),
  industry: z.enum(
    [
      "fashion",
      "music",
      "real-estate",
      "tech",
      "entertainment",
      "custom",
    ] as const,
    {
      required_error: "Please select an industry",
    }
  ),
  targetAudience: z.string().min(1, "Please specify the target audience"),
  usageIntent: z.enum(
    ["product-launch", "music-video", "social-media", "commercial"] as const,
    {
      required_error: "Please select a usage intent",
    }
  ),
});

export type MoodboardFormData = z.infer<typeof moodboardSchema>;

export interface MoodboardList extends MoodboardFormData {
  id: number;
  name: string;
  description: string;
  user_id: number;
}
