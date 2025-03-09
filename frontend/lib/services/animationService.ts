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
  try {
    const url = new URL(`${API_URL}/templates/animations`);

    if (type) {
      url.searchParams.append("animation_type", type);
    }

    const response = await fetch(url.toString());

    if (!response.ok) {
      throw new Error(`Failed to fetch animations: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error("Error fetching animations:", error);
    return [];
  }
};

/**
 * Fetch a specific animation by ID
 * @param id Animation ID
 * @returns Promise with animation data
 */
export const fetchAnimationById = async (
  id: string
): Promise<Animation | null> => {
  try {
    const response = await fetch(`${API_URL}/templates/animations/${id}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch animation: ${response.statusText}`);
    }

    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching animation ${id}:`, error);
    return null;
  }
};
