import type {
  SceneConfiguration,
  OnRemoveAssetFunction,
} from "@/lib/types/sceneConfig";
import { create } from "zustand";

type SceneConfigStore = {
  sceneConfiguration: SceneConfiguration;
  updateSceneConfiguration: (key: keyof SceneConfiguration, value: any) => void;
  removeSceneConfiguration: OnRemoveAssetFunction;
  setSceneConfiguration: (config: SceneConfiguration) => void;
  resetSceneConfiguration: () => void;
};

export const useSceneConfigStore = create<SceneConfigStore>((set) => ({
  sceneConfiguration: {},

  updateSceneConfiguration: (key, value) =>
    set((state) => ({
      sceneConfiguration: {
        ...state.sceneConfiguration,
        [key]: value,
      },
    })),

  removeSceneConfiguration: (assetType, assetId) =>
    set((state) => {
      const newConfig = { ...state.sceneConfiguration };
      switch (assetType) {
        case "camera":
          delete newConfig.camera;
          break;
        case "light":
          delete newConfig.lights;
          break;
      }
      return { sceneConfiguration: newConfig };
    }),

  setSceneConfiguration: (config) => set({ sceneConfiguration: config }),

  resetSceneConfiguration: () => set({ sceneConfiguration: {} }),
}));
