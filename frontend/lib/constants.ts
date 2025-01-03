import { Music, Package, Shirt, Share2 } from "lucide-react";
import { ProjectType } from "./types/ProjectConfig";

export const projectTypes: Record<string, ProjectType> = {
  music: {
    icon: Music,
    subtypes: ["Art Cover", "Visualizer", "Music Video"],
  },
  product: {
    icon: Package,
    subtypes: ["Product Shoot", "Product Reel", "Product Campaign"],
  },
  fashion: {
    icon: Shirt,
    subtypes: ["Look Shoot", "Look Reel", "Fashion Show"],
  },
  socialMedia: {
    icon: Share2,
    subtypes: ["Post", "Reel", "Campaign"],
  },
};

export const projectTemplates = {
  music: [
    {
      id: "music-1",
      name: "Modern Minimal",
      thumbnail:
        "https://images.unsplash.com/photo-1470225620780-dba8ba36b745?w=300&h=200&fit=crop",
    },
    {
      id: "music-2",
      name: "Dynamic Beat",
      thumbnail:
        "https://images.unsplash.com/photo-1511379938547-c1f69419868d?w=300&h=200&fit=crop",
    },
  ],
  product: [
    {
      id: "product-1",
      name: "Clean Studio",
      thumbnail:
        "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=300&h=200&fit=crop",
    },
    {
      id: "product-2",
      name: "Lifestyle",
      thumbnail:
        "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=300&h=200&fit=crop",
    },
  ],
  fashion: [
    {
      id: "fashion-1",
      name: "Editorial",
      thumbnail:
        "https://images.unsplash.com/photo-1469334031218-e382a71b716b?w=300&h=200&fit=crop",
    },
    {
      id: "fashion-2",
      name: "Street Style",
      thumbnail:
        "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=300&h=200&fit=crop",
    },
  ],
  socialMedia: [
    {
      id: "social-1",
      name: "Story Format",
      thumbnail:
        "https://images.unsplash.com/photo-1611162616305-c69b3fa7fbe0?w=300&h=200&fit=crop",
    },
    {
      id: "social-2",
      name: "Grid Layout",
      thumbnail:
        "https://images.unsplash.com/photo-1611162616475-46b635cb6868?w=300&h=200&fit=crop",
    },
  ],
};
