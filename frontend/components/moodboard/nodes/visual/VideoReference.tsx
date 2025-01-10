import { Video, Plus, X, AlertCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useState } from "react";

interface VideoReferencesProps {
  videos: string[];
  onVideosChange: (videos: string[]) => void;
}

export function VideoReferences({
  videos,
  onVideosChange,
}: VideoReferencesProps) {
  const [newUrl, setNewUrl] = useState("");

  const addVideo = () => {
    if (newUrl && videos.length < 5) {
      onVideosChange([...videos, newUrl]);
      setNewUrl("");
    }
  };

  const removeVideo = (index: number) => {
    onVideosChange(videos.filter((_, i) => i !== index));
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-medium text-white">
        Video References ({videos.length}/5)
      </h3>

      <div className="flex gap-2">
        <input
          type="url"
          value={newUrl}
          onChange={(e) => setNewUrl(e.target.value)}
          placeholder="Paste video URL..."
          className="flex-1 bg-cr8-dark/30 backdrop-blur-md text-white rounded-md p-2 text-sm border border-cr8-charcoal/50"
        />
        <Button
          variant="glass"
          size="icon"
          onClick={addVideo}
          disabled={!newUrl || videos.length >= 5}
        >
          <Plus className="h-4 w-4" />
        </Button>
      </div>
      {newUrl && (
        <div className="flex items-center gap-2 text-cr8-blue text-sm mt-1">
          <AlertCircle className="h-4 w-4" />
          <span>Click the plus icon to add the link</span>
        </div>
      )}
      <div className="space-y-2">
        {videos.map((url, index) => (
          <div
            key={index}
            className="flex items-center gap-2 p-2 rounded-md bg-charcoal-800/30 backdrop-blur-md border border-charcoal-700/50"
          >
            <Video className="h-4 w-4 text-blue-400 flex-shrink-0" />
            <span className="text-sm text-white truncate flex-1">{url}</span>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => removeVideo(index)}
              className="flex-shrink-0"
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
