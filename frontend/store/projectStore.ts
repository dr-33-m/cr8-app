import { create } from "zustand";

interface ProjectState {
  name: string;
  template: string;
  setProjectName: (name: string) => void;
  setProjectTemplate: (template: string) => void;
  resetProject: () => void;
}

export const useProjectStore = create<ProjectState>((set) => ({
  name: "",
  template: "",
  setProjectName: (name) => set({ name }),
  setProjectTemplate: (template) => set({ template }),
  resetProject: () => set({ name: "", template: "" }),
}));
