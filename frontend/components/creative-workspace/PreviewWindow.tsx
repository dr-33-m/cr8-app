import { Button } from "@/components/ui/button";
import { Maximize2, Minimize2, Image as ImageIcon } from "lucide-react";
import { cn } from "@/lib/utils";

interface PreviewWindowProps {
  isFullscreen: boolean;
  viewportImage: string | null;
}

export function PreviewWindow({
  isFullscreen,
  viewportImage,
}: PreviewWindowProps) {
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
      {viewportImage ? (
        <img
          src={viewportImage}
          alt="Preview"
          className="w-full h-full object-cover"
        />
      ) : (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="w-20 h-20 rounded-full bg-white/5 flex items-center justify-center mb-4">
            <ImageIcon className="w-10 h-10 text-[#FFD100]" />
          </div>
          <div className="text-[#FFD100] text-lg font-medium">
            Preview Window
          </div>
          <p className="text-white/60 mt-2 text-sm">
            Click the maximize button to enter fullscreen mode
          </p>
        </div>
      )}

      {/* Grid overlay for visual interest */}
      {!viewportImage && (
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0wIDBoNDB2NDBoLTQweiIvPjxwYXRoIGQ9Ik00MCAyMGgtNDBtMjAtMjB2NDAiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLW9wYWNpdHk9Ii4xIi8+PC9nPjwvc3ZnPg==')] opacity-10" />
      )}
    </div>
  );
}
