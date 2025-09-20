import { create } from "zustand";

// Define the scene object type that matches the backend structure
export interface SceneObject {
  name: string;
  type: string;
  visible: boolean;
  active: boolean;
  selected: boolean;
  location: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
}

export interface SceneContextState {
  objects: SceneObject[];
  timestamp: number;
  setSceneObjects: (objects: SceneObject[], timestamp: number) => void;
  clearSceneObjects: () => void;
  getObjectByName: (name: string) => SceneObject | undefined;
  getObjectsByType: (type: string) => SceneObject[];
  reset: () => void;
}

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
