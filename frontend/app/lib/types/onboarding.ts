import { BlendFileInfo } from "@/lib/services/blendFileService";

// Onboarding interfaces
export interface FileStepProps {
  blendFiles: BlendFileInfo[];
  onFileSelect: (file: BlendFileInfo) => void;
}

export interface FolderStepProps {
  folderPath: string;
  onFolderPathChange: (value: string) => void;
  onEnterPress: () => void;
}

export interface LaunchStepProps {
  username: string;
  folderPath: string;
  selectedBlendFile: BlendFileInfo | null;
}

export interface UsernameStepProps {
  username: string;
  onUsernameChange: (value: string) => void;
  onEnterPress: () => void;
}
