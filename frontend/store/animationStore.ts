import { create } from "zustand";
import { persist } from "zustand/middleware";
import { Animation } from "@/lib/types/animations";
import { fetchAnimations } from "@/lib/services/animationService";

interface AnimationState {
  animations: {
    camera: Animation[];
    light: Animation[];
    product: Animation[];
  };
  isLoading: boolean;
  error: string | null;
  selectedAnimations: {
    camera: string | null;
    light: string | null;
    product: string | null;
  };

  // Actions
  fetchAllAnimations: () => Promise<void>;
  selectAnimation: (type: "camera" | "light" | "product", id: string) => void;
  clearSelections: () => void;
  reset: () => void;
}

export const useAnimationStore = create<AnimationState>()(
  persist(
    (set, get) => ({
      animations: {
        camera: [],
        light: [],
        product: [],
      },
      isLoading: false,
      error: null,
      selectedAnimations: {
        camera: null,
        light: null,
        product: null,
      },

      fetchAllAnimations: async () => {
        // If already loading, don't trigger another fetch
        if (get().isLoading) return;

        set({ isLoading: true, error: null });
        try {
          const [camera, light, product] = await Promise.all([
            fetchAnimations("camera"),
            fetchAnimations("light"),
            fetchAnimations("product"),
          ]);

          set({
            animations: { camera, light, product },
            isLoading: false,
          });
        } catch (error) {
          set({
            error: "Failed to fetch animations",
            isLoading: false,
          });
        }
      },

      selectAnimation: (type, id) => {
        // Only update if the selection actually changes
        if (get().selectedAnimations[type] !== id) {
          set((state) => ({
            selectedAnimations: {
              ...state.selectedAnimations,
              [type]: id,
            },
          }));
        }
      },

      clearSelections: () =>
        set({
          selectedAnimations: {
            camera: null,
            light: null,
            product: null,
          },
        }),

      reset: () =>
        set({
          animations: {
            camera: [],
            light: [],
            product: [],
          },
          isLoading: false,
          error: null,
          selectedAnimations: {
            camera: null,
            light: null,
            product: null,
          },
        }),
    }),
    {
      name: "animation-storage",
      partialize: (state) => ({
        selectedAnimations: state.selectedAnimations,
      }),
    }
  )
);
