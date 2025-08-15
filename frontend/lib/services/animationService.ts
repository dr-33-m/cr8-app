import { Animation } from "../types/animations";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

/**
 * Fetch animations from the server
 * @param type Optional animation type filter: "camera", "light", or "product"
 * @returns Promise with array of animations
 */
export const fetchAnimations = async (
  type?: "camera" | "light" | "product"
): Promise<Animation[]> => {
  return [];
};

/**
 * Fetch a specific animation by ID
 * @param id Animation ID
 * @returns Promise with animation data
 */
export const fetchAnimationById = async (
  id: string
): Promise<Animation | null> => {
  return null;
};
