import { create } from "zustand";
import { SceneObject, SceneContextState } from "@/lib/types/stores";

const useSceneContextStore = create<SceneContextState>((set, get) => ({
  objects: [],
  timestamp: 0,

  setSceneObjects: (objects, timestamp) => set({ objects, timestamp }),

  clearSceneObjects: () => set({ objects: [], timestamp: 0 }),

  getObjectByName: (name) => {
    return get().objects.find((obj) => obj.name === name);
  },

  getObjectsByType: (type) => {
    return get().objects.filter((obj) => obj.type === type);
  },

  reset: () => set({ objects: [], timestamp: 0 }),
}));

export default useSceneContextStore;
