import { MoodboardFormData } from "@/types/moodboard";
import { create } from "zustand";

interface MoodboardStore {
  moodboard: Partial<MoodboardFormData>;
  updateMoodboard: (data: Partial<MoodboardFormData>) => void;
  resetMoodboard: () => void;
}

export const useMoodboardStore = create<MoodboardStore>((set) => ({
  moodboard: {
    categoryImages: {
      compositions: [],
      actions: [],
      lighting: [],
      location: [],
    },
    colorPalette: [],
    videoReferences: [],
    keywords: [],
  },
  updateMoodboard: (data) =>
    set((state) => ({
      moodboard: { ...state.moodboard, ...data },
    })),
  resetMoodboard: () =>
    set({
      moodboard: {
        categoryImages: {
          compositions: [],
          actions: [],
          lighting: [],
          location: [],
        },
        colorPalette: [],
        videoReferences: [],
        keywords: [],
      },
    }),
}));
