// Store-related type definitions

// User Store Types
export interface UserStoreState {
  userId: string;
  username: string;
  email: string;
  blendFolderPath: string;
  selectedBlendFile: string;
  fullBlendFilePath: string;
  /** RustFS object key of the selected cloud blend file (remote mode). */
  selectedBlendObjectKey: string;
  isEmptyProject: boolean;
  _hasHydrated: boolean;
  setUser: (user: { id: string; name: string; email?: string | null }) => void;
  setUsername: (username: string) => void;
  setBlendFolder: (path: string) => void;
  setSelectedBlendFile: (filename: string, fullPath: string) => void;
  /** Select a cloud blend file by its object key (remote mode). */
  setSelectedBlendObject: (filename: string, objectKey: string) => void;
  setEmptyProject: (value: boolean) => void;
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
