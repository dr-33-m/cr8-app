import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export const isBrowser = typeof window !== "undefined";

export const transformSceneConfiguration = (data: any): any[] => {
  const assets: any[] = [];

  // Transform camera
  if (data.camera) {
    assets.push({
      id: "camera-1", // generate a unique id
      type: "camera",
      ...data.camera,
    });
  }

  // Transform lights
  if (data.lights) {
    assets.push({
      id: "light-1", // generate a unique id
      type: "light",
      ...data.lights,
    });
  }

  return assets;
};
