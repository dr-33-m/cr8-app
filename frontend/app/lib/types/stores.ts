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

// B.L.A.Z.E Chat / Activity Store Types
export type ChatEntryKind = "user" | "assistant" | "error" | "activity";

export interface ChatEntry {
  id: string;
  kind: ChatEntryKind;
  text: string;
  at: number;
  /** For activity entries: which step this was ('tool_call', 'tool_result', …). */
  phase?: string;
}

/**
 * The exact agent payload last sent, kept so a failed turn can be replayed.
 * Shaped to match what useChatMessage passes to sendMessage.
 */
export interface BlazeRequest {
  message: string;
  context: Record<string, unknown>;
  route: "agent";
  refresh_context: boolean;
}

export interface BlazeChatState {
  entries: ChatEntry[];
  /** True from the moment a message is sent until a reply or error lands. */
  isBusy: boolean;
  /** Something arrived while the dialog was closed. */
  hasUnseen: boolean;
  /** Last request sent, so an error can offer a retry. Cleared once one succeeds. */
  lastRequest: BlazeRequest | null;
  addUser: (text: string) => void;
  addAssistant: (text: string) => void;
  addError: (text: string) => void;
  addActivity: (phase: string, text: string) => void;
  setBusy: (busy: boolean) => void;
  setLastRequest: (request: BlazeRequest | null) => void;
  markSeen: () => void;
  clear: () => void;
}

// Scene Context Store Types
export interface SceneObject {
  name: string;
  type: string;
  visible: boolean;
  active: boolean;
  selected: boolean;
  location: [number, number, number];
  /** Always an XYZ euler in radians, whatever the object's rotation_mode is. */
  rotation: [number, number, number];
  /** Blender's rotation_mode ('XYZ', 'QUATERNION', 'AXIS_ANGLE', …). */
  rotation_mode?: string;
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
