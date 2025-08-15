import { Button } from "../ui/button";
import { Download, Video } from "lucide-react";

interface SceneActionsProps {
  isFinalVideoReady: boolean;
  onGenerateVideo: () => void;
}

export function SceneActions({
  onGenerateVideo,
  isFinalVideoReady,
}: SceneActionsProps) {
  return (
    <>
      <Button
        variant="ghost"
        size="icon"
        className="text-[#0077B6] hover:bg-[#0077B6]/10"
        title="Generate Video"
        onClick={onGenerateVideo}
      >
        <Video className="h-8 w-8" />
        <span className="sr-only">Generate Video</span>
      </Button>

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
