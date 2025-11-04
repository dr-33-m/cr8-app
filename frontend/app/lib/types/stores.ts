// Store-related type definitions

// User Store Types
export interface UserStoreState {
  username: string;
  blendFolderPath: string;
  selectedBlendFile: string;
  fullBlendFilePath: string;
  setUsername: (username: string) => void;
  setBlendFolder: (path: string) => void;
  setSelectedBlendFile: (filename: string, fullPath: string) => void;
  clearBlendSelection: () => void;
  reset: () => void;
}

// Scene Context Store Types
export interface SceneObject {
  name: string;
  type: string;
  visible: boolean;
  active: boolean;
  selected: boolean;
  location: [number, number, number];
  rotation: [number, number, number];
  scale: [number, number, number];
}

export interface SceneContextState {
  objects: SceneObject[];
  timestamp: number;
  setSceneObjects: (objects: SceneObject[], timestamp: number) => void;
  clearSceneObjects: () => void;
  getObjectByName: (name: string) => SceneObject | undefined;
  getObjectsByType: (type: string) => SceneObject[];
  reset: () => void;
}

// Inbox Store Types
export interface InboxItem {
  id: string;
  name: string;
  type: "hdris" | "textures" | "models";
  registry: "polyhaven";
  asset: import("@/lib/types/assetBrowser").PolyHavenAsset & { id: string };
  addedAt: number;
}

export interface InboxStore {
  items: InboxItem[];
  toggleItem: (
    asset: import("@/lib/types/assetBrowser").PolyHavenAsset & { id: string }
  ) => void;
  hasItem: (id: string) => boolean;
  removeItem: (id: string) => void;
  clearAll: () => void;
  getItemCount: () => number;
}
