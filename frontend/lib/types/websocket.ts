export type WebSocketStatus =
  | "connected"
  | "connecting"
  | "disconnected"
  | "failed";

export interface WebSocketMessage {
  type?: string;
  command?: string;
  payload?: any;
  status?: string;
  message?: string;
  data?: any;
  params?: any;
  controllables?: any;

  // Asset Placer properties
  empty_name?: string;
  filepath?: string;
  asset_name?: string;
  degrees?: number;
  scale_percent?: number;
  reset?: boolean;
  mode?: string;
  scale_factor?: number;
  center_origin?: boolean;
  empty1_name?: string;
  empty2_name?: string;
}

export interface WebSocketError {
  code: number;
  message: string;
}

export interface WebSocketContextType {
  status: WebSocketStatus;
  websocket: WebSocket | null;
  isConnected: boolean;
  reconnect: () => void;
  disconnect: () => void;
  sendMessage: (message: WebSocketMessage) => void;
  requestTemplateControls: () => void;
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

// Template Control Message Types
export interface TemplateControlMessage extends WebSocketMessage {
  command: "get_template_controls";
}

export interface TemplateControlResponse extends WebSocketMessage {
  command: "template_controls";
  controllables: any;
}

// Preview Message Types
export interface PreviewMessage extends WebSocketMessage {
  type: "frame";
  data: string;
}

export interface PreviewErrorMessage extends WebSocketMessage {
  type: "viewport_stream_error";
  message: string;
}

export interface PreviewCommandMessage extends WebSocketMessage {
  command:
    | "shoot_preview"
    | "playback_preview"
    | "stop_playback_preview"
    | "generate_video";
  params?: any;
}

// Asset Placer Message Types
export interface AssetPlacerCommandMessage extends WebSocketMessage {
  command:
    | "append_asset"
    | "remove_assets"
    | "swap_assets"
    | "rotate_assets"
    | "scale_assets"
    | "get_asset_info";
}

export interface AssetPlacerResponseMessage extends WebSocketMessage {
  command:
    | "append_asset_result"
    | "remove_assets_result"
    | "swap_assets_result"
    | "rotate_assets_result"
    | "scale_assets_result"
    | "asset_info_result";
  status: "success" | "failed";
  data: {
    success: boolean;
    message: string;
    object_name?: string;
    assets?: any[];
  };
}
