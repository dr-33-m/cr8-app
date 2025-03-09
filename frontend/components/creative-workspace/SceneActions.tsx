import { Button } from "../ui/button";
import {
  Clapperboard,
  LoaderPinwheel,
  Pause,
  Play,
  Download,
} from "lucide-react";

interface SceneActionsProps {
  isLoading: boolean;
  isPlaying: boolean;
  isFinalVideoReady: boolean;
  onShootPreview: () => void;
  onPlaybackPreview: () => void;
  onStopPlaybackPreview: () => void;
  onGenerateVideo: () => void;
}

export function SceneActions({
  onShootPreview,
  onPlaybackPreview,
  onStopPlaybackPreview,
  onGenerateVideo,
  isLoading,
  isPlaying,
  isFinalVideoReady,
}: SceneActionsProps) {
  return (
    <>
      {!isFinalVideoReady ? (
        <>
          <Button
            variant="ghost"
            size="icon"
            className="text-[#0077B6] hover:bg-[#0077B6]/10"
            title="Shoot Preview"
            onClick={onShootPreview}
            // onClick={onGenerateVideo}
            disabled={isLoading}
          >
            {isLoading ? (
              <LoaderPinwheel className="h-8 w-8 animate-spin" />
            ) : (
              <Clapperboard className="h-8 w-8" />
            )}

            <span className="sr-only">
              {isLoading ? "Shooting Preview" : "Shoot Preview"}
            </span>
          </Button>

          <Button
            variant="ghost"
            size="icon"
            className="text-[#FFD100] hover:bg-[#FFD100]/10"
            title={isPlaying ? "Pause Preview" : "Play Preview"}
            onClick={isPlaying ? onStopPlaybackPreview : onPlaybackPreview}
            disabled={isLoading}
          >
            {isPlaying ? (
              <Pause className="h-6 w-6" />
            ) : (
              <Play className="h-6 w-6" />
            )}
            <span className="sr-only">
              {isPlaying ? "Pause Preview" : "Play Preview"}
            </span>
          </Button>
        </>
      ) : (
        <Button
          variant="ghost"
          size="icon"
          className="text-[#FFD100] hover:bg-[#FFD100]/10"
          title={isPlaying ? "Pause Preview" : "Play Preview"}
          onClick={isPlaying ? onStopPlaybackPreview : onPlaybackPreview}
          disabled={isLoading}
        >
          {isPlaying ? (
            <Pause className="h-6 w-6" />
          ) : (
            <Play className="h-6 w-6" />
          )}
          <span className="sr-only">
            {isPlaying ? "Pause Preview" : "Play Preview"}
          </span>
        </Button>
      )}
      <div className="h-8 w-px bg-white/20" />
      {isFinalVideoReady && (
        <Button className="text-[#FFD100] hover:bg-[#FFD100]/5 bg-[#FFD100]/10">
          <Download className="h-5 w-5 mr-2" />
          Download
        </Button>
      )}
    </>
  );
}
