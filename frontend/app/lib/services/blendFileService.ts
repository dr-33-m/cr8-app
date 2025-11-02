import { toast } from "sonner";

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

class BlendFileService {
  private baseUrl: string;

  constructor() {
    this.baseUrl = import.meta.env.VITE_API_URL || "http://localhost:8000";
  }

  async scanBlendFolder(folderPath: string): Promise<ScanBlendFolderResponse> {
    try {
      const response = await fetch(`${this.baseUrl}/api/v1/scan-blend-folder`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          folder_path: folderPath,
        } as ScanBlendFolderRequest),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({
          detail: "Unknown error occurred",
        }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const data: ScanBlendFolderResponse = await response.json();
      return data;
    } catch (error) {
      const errorMessage =
        error instanceof Error ? error.message : "Failed to scan folder";
      toast.error(`Error scanning blend files: ${errorMessage}`);
      throw error;
    }
  }
}

export const blendFileService = new BlendFileService();
