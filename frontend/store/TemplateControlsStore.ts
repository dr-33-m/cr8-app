import { TemplateControls } from "@/lib/types/templateControls";
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface TemplateControlsState {
  controls: TemplateControls | null;
  isLoading: boolean;
  error: string | null;
  setControls: (controls: TemplateControls) => void;
  clearControls: () => void;
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useTemplateControlsStore = create<TemplateControlsState>()(
  persist(
    (set) => ({
      controls: null,
      isLoading: false,
      error: null,
      setControls: (controls) => set({ controls, error: null }),
      clearControls: () => set({ controls: null }),
      setError: (error) => set({ error }),
      setLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: "template-controls-storage",
      partialize: (state) => ({ controls: state.controls }), // Only persist the controls data
    }
  )
);
