// Onboarding interfaces

// Blend file service interfaces
export interface BlendFileInfo {
  filename: string;
  full_path: string;
}

export interface ScanBlendFolderResponse {
  blend_files: BlendFileInfo[];
  total_count: number;
}

export interface ScanBlendFolderRequest {
  folder_path: string;
}
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
