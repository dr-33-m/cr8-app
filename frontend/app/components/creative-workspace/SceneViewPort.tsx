import { ImageIcon, AlertCircle, XCircle } from "lucide-react";
import { SceneViewPortProps } from "@/lib/types/creativeWorkspace";
import { getStudioMessages, formatElapsed, ERROR_REASONS } from "@/lib/studioLoadingMessages";
import { useLaunchTimerStore } from "@/store/launchTimerStore";

export function SceneViewPort({ videoRef, isConnected, instanceStatus }: SceneViewPortProps) {
  const elapsed = useLaunchTimerStore((state) => state.elapsed);
  const msgTick = useLaunchTimerStore((state) => state.msgTick);

  const phase = instanceStatus?.phase ?? "default";
  const isError = phase === "error";
  const isCancelled = phase === "cancelled";
  const messages = getStudioMessages(phase);

  // msgTick resets to 0 in the store whenever the phase changes, so this always
  // starts at index 0 for each new phase and advances every 4 seconds.
  const msgIndex = Math.floor(msgTick / 4) % messages.length;

  return (
    <>
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        className={`w-full h-full object-cover ${!isConnected ? "hidden" : ""}`}
      />

      {!isConnected ? (
        <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
          {/* Icon */}
          <div className="w-20 h-20 rounded-full flex items-center justify-center">
            {isError ? (
              <AlertCircle className="w-10 h-10 text-destructive" />
            ) : isCancelled ? (
              <XCircle className="w-10 h-10 text-muted-foreground" />
            ) : (
              <ImageIcon className="w-10 h-10 text-primary animate-pulse" />
            )}
          </div>

          {/* Message */}
          <div className="text-center max-w-sm px-6">
            {isError ? (
              <>
                <p className="text-destructive text-base font-medium leading-snug">
                  {ERROR_REASONS[instanceStatus?.error?.reason ?? "unknown"] ?? ERROR_REASONS.unknown}
                </p>
                {instanceStatus?.elapsed ? (
                  <p className="text-muted-foreground text-xs mt-3">
                    After {formatElapsed(instanceStatus.elapsed)}
                  </p>
                ) : null}
              </>
            ) : isCancelled ? (
              <p className="text-muted-foreground text-base font-medium leading-snug">
                Launch cancelled.
              </p>
            ) : (
              <>
                <p className="text-primary text-base font-medium leading-snug min-h-12 transition-all duration-500">
                  {messages[msgIndex]}
                </p>
                {instanceStatus && phase !== "blender_connected" ? (
                  <p className="text-muted-foreground text-xs mt-3">
                    {formatElapsed(elapsed)} elapsed
                  </p>
                ) : !instanceStatus ? (
                  <p className="text-muted-foreground text-sm mt-2">
                    Connecting to your workspace...
                  </p>
                ) : null}
              </>
            )}
          </div>

          {/* Animated dots — only during loading (not error/cancelled) */}
          {!isError && !isCancelled && (
            <div className="flex gap-1.5">
              {[0, 1, 2].map((i) => (
                <span
                  key={i}
                  className="w-1.5 h-1.5 rounded-full bg-primary opacity-60"
                  style={{ animation: `bounce 1.2s ease-in-out ${i * 0.2}s infinite` }}
                />
              ))}
            </div>
          )}
        </div>
      ) : null}

      {!isConnected && (
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAiIGhlaWdodD0iNDAiIHZpZXdCb3g9IjAgMCA0MCA0MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0wIDBoNDB2NDBoLTQweiIvPjxwYXRoIGQ9Ik00MCAyMGgtNDBtMjAtMjB2NDAiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLW9wYWNpdHk9Ii4xIi8+PC9nPjwvc3ZnPg==')] opacity-10" />
      )}
    </>
  );
}
