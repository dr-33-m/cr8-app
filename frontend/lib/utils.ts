import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { SceneConfiguration } from "./types/sceneConfig";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const isBrowser = typeof window !== "undefined";

// Modify the transform function to handle arrays correctly
export const transformSceneConfiguration = (
  data: SceneConfiguration
): any[] => {
  const assets: any[] = [];

  // Transform camera
  if (data.camera) {
    assets.push({
      id: "camera-1",
      type: "camera",
      ...data.camera,
    });
  }

  // Transform lights (as a single object)
  if (data.lights) {
    assets.push({
      id: "light-1",
      type: "light",
      ...data.lights, // Spread the light object directly
    });
  }

  return assets;
};
