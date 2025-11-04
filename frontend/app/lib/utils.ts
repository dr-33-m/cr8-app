import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDownloads(count: number): string {
  if (count >= 1000000) {
    return `${(count / 1000000).toFixed(1)}M`;
  } else if (count >= 1000) {
    return `${(count / 1000).toFixed(1)}K`;
  }
  return count.toString();
}

export function getAssetTypeName(type: number): string {
  switch (type) {
    case 0:
      return "HDRI";
    case 1:
      return "Texture";
    case 2:
      return "Model";
    default:
      return "Asset";
  }
}
