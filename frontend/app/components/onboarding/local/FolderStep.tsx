import { Input } from "@/components/ui/input";

interface FolderStepProps {
  folderPath: string;
  onFolderPathChange: (value: string) => void;
  onEnterPress: () => void;
}

export function FolderStep({
  folderPath,
  onFolderPathChange,
  onEnterPress,
}: FolderStepProps) {
  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      onEnterPress();
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h3 className="text-xl font-semibold mb-2 text-foreground">
          Blend Files Folder
        </h3>
        <p className="text-muted-foreground text-sm">
          Enter the path to your .blend files folder
        </p>
      </div>
      <Input
        type="text"
        placeholder="/path/to/your/blend/files"
        value={folderPath}
        onChange={(e) => onFolderPathChange(e.target.value)}
        onKeyPress={handleKeyPress}
      />
    </div>
  );
}
