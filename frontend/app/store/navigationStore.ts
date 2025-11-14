import { create } from "zustand";
import { ViewportMode } from "@/lib/types/bottomControls";

interface NavigationState {
  viewportMode: ViewportMode;
  topButtonDirection: "PANUP" | "PANFORWARD";
  bottomButtonDirection: "PANDOWN" | "PANBACK";
  panAmount: number;
  setViewportMode: (mode: ViewportMode) => void;
  setTopButtonDirection: (direction: "PANUP" | "PANFORWARD") => void;
  setBottomButtonDirection: (direction: "PANDOWN" | "PANBACK") => void;
  setPanAmount: (amount: number) => void;
  toggleTopButtonDirection: () => void;
  toggleBottomButtonDirection: () => void;
}

export const useNavigationStore = create<NavigationState>((set) => ({
  viewportMode: "solid",
  topButtonDirection: "PANUP",
  bottomButtonDirection: "PANDOWN",
  panAmount: 0.5,
  setViewportMode: (mode) => set({ viewportMode: mode }),
  setTopButtonDirection: (direction) => set({ topButtonDirection: direction }),
  setBottomButtonDirection: (direction) =>
    set({ bottomButtonDirection: direction }),
  setPanAmount: (amount) => set({ panAmount: amount }),
  toggleTopButtonDirection: () =>
    set((state) => ({
      topButtonDirection:
        state.topButtonDirection === "PANUP" ? "PANFORWARD" : "PANUP",
    })),
  toggleBottomButtonDirection: () =>
    set((state) => ({
      bottomButtonDirection:
        state.bottomButtonDirection === "PANDOWN" ? "PANBACK" : "PANDOWN",
    })),
}));
