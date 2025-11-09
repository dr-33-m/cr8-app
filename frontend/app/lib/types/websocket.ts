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
  route?: "direct" | "agent"; // Explicit routing specification
  recovery?: boolean; // For browser_ready recovery mode
  refresh_context?: boolean; // Flag to control scene context refresh
  context?: {
    inbox_items?: Array<{
      id: string;
      name: string;
      type: string;
      registry: string;
    }>;
    scene_objects?: Array<{
      name: string;
      type: string;
      selected: boolean;
      active: boolean;
      visible: boolean;
    }>;
    mentions?: {
      assets?: Array<{
        id: string;
        name: string;
        type: string;
        source: string;
        itemType: string;
      }>;
      objects?: Array<{
        id: string;
        name: string;
        type: string;
        source: string;
        itemType: string;
      }>;
    };
  };
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

// Hook interfaces
export interface ConnectionListener {
  connected: (clientId: string) => void;
  disconnected: () => void;
}

export interface PeerListener {
  producerAdded?: (producer: Peer) => void;
  producerRemoved?: (producer: Peer) => void;
  consumerAdded?: (consumer: Peer) => void;
  consumerRemoved?: (consumer: Peer) => void;
}

export interface Peer {
  readonly id: string;
  readonly meta: Record<string, unknown>;
}

// ============================================================================
// STANDARDIZED SOCKET.IO MESSAGE TYPES (Phase 1)
// ============================================================================

/**
 * Message types following state-based naming convention
 */
export enum MessageType {
  // Connection lifecycle
  SESSION_CREATED = "session_created",
  SESSION_READY = "session_ready",
  BLENDER_CONNECTED = "blender_connected",
  BLENDER_DISCONNECTED = "blender_disconnected",

  // Direct commands (UI controls)
  COMMAND_SENT = "command_sent",
  COMMAND_RECEIVED = "command_received",
  COMMAND_COMPLETED = "command_completed",
  COMMAND_FAILED = "command_failed",

  // Agent interactions (natural language)
  AGENT_QUERY_SENT = "agent_query_sent",
  AGENT_PROCESSING = "agent_processing",
  AGENT_RESPONSE_READY = "agent_response_ready",
  AGENT_ERROR = "agent_error",

  // System updates
  REGISTRY_UPDATED = "registry_updated",
  SCENE_CONTEXT_UPDATED = "scene_context_updated",
  INBOX_CLEARED = "inbox_cleared",

  // Errors
  CONNECTION_ERROR = "connection_error",
  VALIDATION_ERROR = "validation_error",
  EXECUTION_ERROR = "execution_error",
}

/**
 * Universal Socket.IO message structure
 * All messages must follow this format for consistency
 */
export interface SocketMessage {
  message_id: string; // UUID for tracking (REQUIRED)
  type: MessageType; // Message category (state-based)
  payload: MessagePayload; // Message-specific data
  metadata?: MessageMetadata; // Optional tracking information
}

/**
 * Message metadata for tracking and debugging
 */
export interface MessageMetadata {
  timestamp: number;
  source: "browser" | "backend" | "blender";
  route: "direct" | "agent";
  refresh_context?: boolean; // Flag to control scene context refresh
}

/**
 * Base payload type - can be extended for specific message types
 */
export type MessagePayload =
  | CommandPayload
  | AgentQueryPayload
  | ResponsePayload
  | SystemPayload;

/**
 * Payload for direct command messages (UI controls)
 */
export interface CommandPayload {
  addon_id: string;
  command: string;
  params: Record<string, any>;
}

/**
 * Payload for agent query messages (natural language)
 */
export interface AgentQueryPayload {
  message: string;
  context?: {
    inbox_items?: Array<{
      id: string;
      name: string;
      type: string;
      registry: string;
    }>;
    scene_objects?: SceneObject[];
  };
}

/**
 * Payload for response messages
 */
export interface ResponsePayload {
  status: "success" | "error";
  data?: any;
  error?: ErrorDetails;
}

/**
 * Error details with user-friendly messages
 */
export interface ErrorDetails {
  code: string;
  user_message: string; // Simple English from B.L.A.Z.E
  technical_message: string; // For debugging/logs
  recovery_suggestions?: string[];
}

/**
 * Payload for system update messages
 */
export interface SystemPayload {
  status?: string;
  message?: string;
  data?: any;
}

/**
 * Helper type for creating messages with specific payloads
 */
export type TypedSocketMessage<T extends MessagePayload> = Omit<
  SocketMessage,
  "payload"
> & {
  payload: T;
};

/**
 * Utility function to generate message IDs
 */
export function generateMessageId(): string {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Type guard to check if a message is a SocketMessage
 */
export function isSocketMessage(obj: any): obj is SocketMessage {
  return (
    obj &&
    typeof obj === "object" &&
    "message_id" in obj &&
    "type" in obj &&
    "payload" in obj
  );
}

/**
 * Type guard to check if a payload is a CommandPayload
 */
export function isCommandPayload(payload: any): payload is CommandPayload {
  return (
    payload &&
    typeof payload === "object" &&
    "addon_id" in payload &&
    "command" in payload &&
    "params" in payload
  );
}

/**
 * Type guard to check if a payload is an AgentQueryPayload
 */
export function isAgentQueryPayload(
  payload: any
): payload is AgentQueryPayload {
  return payload && typeof payload === "object" && "message" in payload;
}

/**
 * Type guard to check if a payload is a ResponsePayload
 */
export function isResponsePayload(payload: any): payload is ResponsePayload {
  return payload && typeof payload === "object" && "status" in payload;
}
