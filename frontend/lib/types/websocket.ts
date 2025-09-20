export type WebSocketStatus =
  | "connected"
  | "connecting"
  | "disconnected"
  | "failed";

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

export interface SceneContextUpdateData {
  objects: SceneObject[];
  timestamp: number;
}

export interface WebSocketMessage {
  type?: string;
  command?: string;
  addon_id?: string; // For addon command routing
  payload?: any;
  status?: string;
  message?: string;
  message_id?: string;
  data?: any;
  params?: any;
  recovery?: boolean; // For browser_ready recovery mode
}

export interface WebSocketError {
  code: number;
  message: string;
}

export interface WebSocketProviderProps {
  children: React.ReactNode;
  onMessage?: (data: any) => void;
}

export interface WebSocketConfig {
  initialReconnectDelay: number;
  maxReconnectDelay: number;
  maxReconnectAttempts: number;
}

export interface WebSocketState {
  status: WebSocketStatus;
  reconnectAttempts: number;
  messageQueue: WebSocketMessage[];
}

export interface WebSocketHandlers {
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: WebSocketError) => void;
  onMessage?: (data: any) => void;
}
