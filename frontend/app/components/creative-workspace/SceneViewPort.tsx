import { ImageIcon } from "lucide-react";
import { SceneViewPortProps } from "@/lib/types/creativeWorkspace";

export function SceneViewPort({ videoRef, isConnected }: SceneViewPortProps) {
  return (
    <>
      {/* Always render the WebRTC video element so ref exists */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`w-full h-full object-cover ${!isConnected ? "hidden" : ""}`}
      />

      {!isConnected ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="w-20 h-20 rounded-full flex items-center justify-center mb-4">
            <ImageIcon className="w-10 h-10 text-primary" />
          </div>
          <div className="text-primary text-lg font-medium">
            Connecting to Preview...
          </div>
          <p className="text-muted-foreground mt-2 text-sm">
            Waiting for live stream from Blender.
          </p>
        </div>
      ) : null}

      {/* Grid overlay for visual interest */}
      {!isConnected && (
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0wIDBoNDB2NDBoLTQweiIvPjxwYXRoIGQ9Ik00MCAyMGgtNDBtMjAtMjB2NDAiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLW9wYWNpdHk9Ii4xIi8+PC9nPjwvc3ZnPg==')] opacity-10" />
      )}
    </>
  );
}
