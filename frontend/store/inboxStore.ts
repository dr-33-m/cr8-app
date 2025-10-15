import { create } from "zustand";
import { persist } from "zustand/middleware";
import { PolyHavenAsset } from "@/lib/services/polyhavenService";

export interface InboxItem {
  id: string;
  name: string;
  type: "hdris" | "textures" | "models";
  registry: "polyhaven";
  asset: PolyHavenAsset & { id: string };
  addedAt: number;
}

interface InboxStore {
  items: InboxItem[];
  toggleItem: (asset: PolyHavenAsset & { id: string }) => void;
  hasItem: (id: string) => boolean;
  removeItem: (id: string) => void;
  clearAll: () => void;
  getItemCount: () => number;
}

const useInboxStore = create<InboxStore>()(
  persist(
    (set, get) => ({
      items: [],

      toggleItem: (asset) => {
        const items = get().items;
        const existingIndex = items.findIndex((item) => item.id === asset.id);

        if (existingIndex >= 0) {
          // Remove from inbox
          set({
            items: items.filter((item) => item.id !== asset.id),
          });
        } else {
          // Add to inbox
          const newItem: InboxItem = {
            id: asset.id,
            name: asset.name,
            type:
              asset.type === 0
                ? "hdris"
                : asset.type === 1
                  ? "textures"
                  : "models",
            registry: "polyhaven",
            asset: asset,
            addedAt: Date.now(),
          };
          set({
            items: [...items, newItem],
          });
        }
      },

      hasItem: (id) => {
        return get().items.some((item) => item.id === id);
      },

      removeItem: (id) => {
        set({
          items: get().items.filter((item) => item.id !== id),
        });
      },

      clearAll: () => {
        set({ items: [] });
      },

      getItemCount: () => {
        return get().items.length;
      },
    }),
    {
      name: "cr8-inbox-storage",
    }
  )
);

export default useInboxStore;
