import { cn } from "@/lib/utils";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";

export function PreviewWindow({ children }) {
  const isFullscreen = useVisibilityStore((state) => state.isFullscreen);
  return (
    <div
      className={cn(
        "absolute bg-gradient-to-br from-[#2C2C2C] to-[#1C1C1C]",
        "transition-all duration-500 ease-in-out",
        isFullscreen
          ? "fixed inset-0 w-screen h-screen"
          : "left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-2/3 h-2/3 rounded-lg overflow-hidden shadow-2xl"
      )}
    >
      {children}
    </div>
  );
}
