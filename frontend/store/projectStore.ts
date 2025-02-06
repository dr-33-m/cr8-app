import { create } from "zustand";
import { persist } from "zustand/middleware";

interface ProjectState {
  name: string | null;
  template: string | null;
  setProjectName: (name: string) => void;
  setProjectTemplate: (template: string) => void;
  clearProject: () => void;
}

export const useProjectStore = create<ProjectState>()(
  persist(
    (set) => ({
      name: null,
      template: null,
      setProjectName: (name) => set({ name }),
      setProjectTemplate: (template) => set({ template }),
      clearProject: () => set({ name: null, template: null }),
    }),
    {
      name: "project-storage", // unique name for localStorage key
      partialize: (state) => ({
        // only persist these fields
        name: state.name,
        template: state.template,
      }),
    }
  )
);
