import {
  createContext,
  useContext,
  ReactNode,
  useCallback,
  useState,
  useEffect,
  useRef,
} from "react";
import { useSocketIO } from "@/hooks/useSocketIO";
import {
  WebSocketStatus,
  WebSocketMessage,
  MessageType,
  SocketMessage,
  SystemPayload,
  isSocketMessage,
  isResponsePayload,
} from "@/lib/types/websocket";
import useInboxStore from "@/store/inboxStore";
import useBlazeChatStore from "@/store/blazeChatStore";
import { useNavigationStore } from "@/store/navigationStore";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import useUserStore from "@/store/userStore";
import { toast } from "sonner";
import { Socket } from "socket.io-client";
import { useQueryClient } from "@tanstack/react-query";
import { sceneContextKeys } from "@/websocket/query-manager/scene-context";
import { useLaunchTimerStore } from "@/store/launchTimerStore";
import { checkEngineHealthFn } from "@/server/engine/functions";
import { ADDON_IDS } from "@/lib/constants/addons";

type ConnectionState =
  | "connecting" // First attempt in flight — never been connected yet
  | "disconnected" // Was connected (or an attempt failed), now not connected
  | "browser_connected" // Browser connected, waiting for Blender
  | "fully_connected" // Both connected
  | "blender_reconnecting" // Blender dropped (network blip), auto-reconnecting
  | "blender_disconnected" // Blender crashed/closed (after grace period)
  | "server_unavailable" // Server down for 5+ minutes
  | "reconnecting"; // Attempting reconnect

export interface InstanceStatusError {
  reason: string;      // "timeout" | "ssh_failed" | "blender_failed" | "no_gpu" | "unknown"
  recoverable: boolean;
}

export interface InstanceStatus {
  phase: string;   // "created" | "loading" | "running" | "error" | "cancelled"
  elapsed: number; // seconds since launch started
  error?: InstanceStatusError; // present when phase === "error"
}

export type RenderEngine = "EEVEE" | "CYCLES";
export type RenderResolution = "hd" | "2k" | "4k";
export type RenderAspect = "16:9" | "9:16" | "1:1" | "4:5" | "3:2";

export interface RenderOptions {
  /** Omit to render from the scene's active camera. */
  camera?: string;
  engine: RenderEngine;
  resolution: RenderResolution;
  aspect: RenderAspect;
}

export interface RenderResult {
  ok: boolean;
  /** Storage key of the finished render, present on success. */
  key?: string;
  project?: string;
  /** True when the backend refused because the project has no cloud target. */
  noTarget?: boolean;
  message?: string;
}

interface WebSocketContextType {
  status: WebSocketStatus;
  socket: Socket | null;
  isConnected: boolean;
  blenderConnected: boolean;
  /** True once THIS workspace's Blender has connected at least once. Stays true
   * across later reconnect blips, so the stream isn't hidden during a network
   * hiccup — only before the very first connect of the session. */
  blenderConnectedOnce: boolean;
  isFullyConnected: boolean;
  connectionState: ConnectionState;
  isHealthCheckInProgress: boolean;
  instanceStatus: InstanceStatus | null;
  cancelLaunch: () => void;
  reconnect: () => void;
  disconnect: () => void;
  sendMessage: (message: WebSocketMessage) => void;
  /** Save the running .blend to cloud storage. Pass a filename for Save As
   * (new/renamed file); omit it to overwrite the currently-open file. Resolves
   * true on a confirmed cloud save, false otherwise. */
  saveFile: (filename?: string) => Promise<boolean>;
  /** True while a save is in flight. The save runs on Blender's main thread, so
   * the UI blocks interaction (SavingOverlay) until it clears. */
  isSaving: boolean;
  /** True when this project has somewhere in the cloud to save to — either it
   * was opened from there, or a Save As this session gave it a key. Session
   * state on purpose: it mirrors the backend's `session['blend_object_key']`,
   * and both die when the workspace does. False means Save must collect a name
   * first, and leaving without one discards the work. */
  hasCloudTarget: boolean;
  /** Render the current frame and store it in the user's render library.
   * Resolves with the stored key on success. `noTarget` means the project has
   * never been saved to the cloud, so there is no folder to file renders under —
   * the caller should route the user through Save As and retry. */
  renderImage: (options: RenderOptions) => Promise<RenderResult>;
  /** True while a render is in flight — blocks the UI via RenderingOverlay,
   * because the render occupies Blender's main thread. */
  isRendering: boolean;
  /** Tell the backend to shut down this user's Blender/instance (which also ends
   * the stream). Fire-and-forget; call after any final save, before leaving. */
  exitWorkspace: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: ReactNode;
  remoteUser?: string;
  onMessage?: (data: any) => void;
}

export function WebSocketProvider({
  children,
  remoteUser,
  onMessage,
}: WebSocketProviderProps) {
  const queryClient = useQueryClient();
  const [blenderConnected, setBlenderConnected] = useState(false);
  const [blenderConnectedOnce, setBlenderConnectedOnce] = useState(false);
  const [contextUpdateSent, setContextUpdateSent] = useState(false);
  const [sessionCreated, setSessionCreated] = useState(false);
  // Starts as "connecting", not "disconnected". On a first navigation into the
  // workspace the socket has simply not opened yet — rendering that as
  // "Cannot connect to server" with a Reconnect button flashed a failure state
  // at the user while their Blender instance was in fact launching normally.
  const [connectionState, setConnectionState] =
    useState<ConnectionState>("connecting");
  const [isHealthCheckInProgress, setIsHealthCheckInProgress] = useState(false);
  const [instanceStatus, setInstanceStatus] = useState<InstanceStatus | null>(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isRendering, setIsRendering] = useState(false);
  // Set by a successful Save As. The backend records the new key on the socket
  // session, but never tells us what it is — so this flag, not a key, is what
  // says "there is a target now".
  const [savedAs, setSavedAs] = useState(false);
  const selectedBlendObjectKey = useUserStore((s) => s.selectedBlendObjectKey);

  // Use refs for immediate state tracking to avoid race conditions
  const isReconnectionRef = useRef(false);
  const shouldSendBrowserReadyRef = useRef(false);
  const blenderReconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  // In-flight saveFile() calls, keyed by the message_id we emitted. Resolved
  // when the matching command_completed/command_failed comes back.
  const pendingSavesRef = useRef<Map<string, (ok: boolean) => void>>(new Map());
  // Same pattern for renders. Kept in a separate map so a save and a render
  // can never resolve each other's promise.
  const pendingRendersRef = useRef<Map<string, (r: RenderResult) => void>>(
    new Map()
  );

  const processMessage = useCallback(
    (data: any) => {
      // Check if it's a standardized message
      if (!isSocketMessage(data)) {
        console.warn("Received non-standardized message:", data);
        onMessage?.(data);
        return;
      }

      const message = data as SocketMessage;
      const payload = message.payload;

      // Resolve a pending saveFile() call before the generic command handlers,
      // so a save owns its own success/error toast (and doesn't double-toast via
      // the shared COMMAND_FAILED handler below).
      if (
        (message.type === MessageType.COMMAND_COMPLETED ||
          message.type === MessageType.COMMAND_FAILED) &&
        message.message_id &&
        pendingSavesRef.current.has(message.message_id)
      ) {
        const resolve = pendingSavesRef.current.get(message.message_id)!;
        pendingSavesRef.current.delete(message.message_id);

        let ok = false;
        let msg = "Save failed";
        if (message.type === MessageType.COMMAND_FAILED) {
          // Backend-side failure (validation/routing) — error is in payload.error.
          msg =
            isResponsePayload(payload) && payload.error
              ? payload.error.user_message
              : "Save failed";
        } else {
          // Addon reply: always command_completed, real outcome in payload.data.
          const d = isResponsePayload(payload) ? payload.data : undefined;
          ok = d?.ok === true;
          msg = d?.message || (ok ? "Saved to cloud" : "Save failed");
        }
        if (ok) toast.success(msg);
        else toast.error(msg);
        resolve(ok);
        onMessage?.(data);
        return;
      }

      // Same for a pending renderImage() call, ahead of the generic handlers.
      if (
        (message.type === MessageType.COMMAND_COMPLETED ||
          message.type === MessageType.COMMAND_FAILED) &&
        message.message_id &&
        pendingRendersRef.current.has(message.message_id)
      ) {
        const resolve = pendingRendersRef.current.get(message.message_id)!;
        pendingRendersRef.current.delete(message.message_id);

        let result: RenderResult = { ok: false, message: "Render failed" };
        if (message.type === MessageType.COMMAND_FAILED) {
          const error = isResponsePayload(payload) ? payload.error : undefined;
          const noTarget = error?.code === "NO_TARGET";
          result = {
            ok: false,
            noTarget,
            message: error?.user_message || "Render failed",
          };
          // NO_TARGET isn't a failure the user needs to see — the caller turns
          // it into a Save As prompt and retries. Toasting it would put an
          // error on screen a moment before we ask them to name the file.
          if (!noTarget) toast.error(result.message!);
        } else {
          const d = isResponsePayload(payload) ? payload.data : undefined;
          result = {
            ok: d?.ok === true,
            key: d?.key,
            project: d?.project,
            message: d?.message || (d?.ok ? "Render saved" : "Render failed"),
          };
          if (result.ok) toast.success(result.message!);
          else toast.error(result.message!);
        }
        resolve(result);
        onMessage?.(data);
        return;
      }

      // Handle messages by type using switch
      switch (message.type) {
        case MessageType.SESSION_CREATED:
          toast.success("Connected to Cr8 Engine");
          setSessionCreated(true);
          setConnectionState("browser_connected");
          if (!isReconnectionRef.current) {
            shouldSendBrowserReadyRef.current = true;
          }
          break;

        case MessageType.INSTANCE_STATUS: {
          const p = payload as any;
          const phase: string = p.status ?? null;
          const backendElapsed: number = p.data?.elapsed ?? 0;

          if (phase) {
            const newStatus: InstanceStatus = { phase, elapsed: backendElapsed };
            if (phase === "error" && p.data?.reason) {
              newStatus.error = {
                reason: p.data.reason,
                recoverable: p.data.recoverable ?? true,
              };
            }
            setInstanceStatus(newStatus);

            if (phase === "error" || phase === "cancelled") {
              // Terminal — freeze and stop the timer.
              useLaunchTimerStore.getState().stop();
            } else if (phase === "retrying") {
              // New instance about to start — reset anchor so elapsed restarts from 0.
              useLaunchTimerStore.getState().stop();
            } else {
              useLaunchTimerStore.getState().seed(backendElapsed, phase);
            }
          } else if (p.data?.elapsed !== undefined) {
            // Backend omits 'status' when actual_status is null (new instance first polls).
            // Keep the timer running — backend fix handles this, but guard defensively.
            useLaunchTimerStore.getState().seed(backendElapsed, "loading");
          }
          break;
        }

        case MessageType.BLENDER_CONNECTED:
          // Clear any pending reconnect grace timer
          if (blenderReconnectTimerRef.current) {
            clearTimeout(blenderReconnectTimerRef.current);
            blenderReconnectTimerRef.current = null;
          }
          useLaunchTimerStore.getState().stop();
          // Restart the message cycle for the blender_connected phase so the
          // "connecting camera" messages animate. Elapsed is hidden for this phase.
          useLaunchTimerStore.getState().seed(0, "blender_connected");
          setInstanceStatus({
            phase: "blender_connected",
            elapsed: instanceStatus?.elapsed ?? 0,
          });
          setBlenderConnected(true);
          setBlenderConnectedOnce(true);
          setConnectionState("fully_connected");
          if (
            isResponsePayload(payload) &&
            payload.data?.message?.includes("Reconnected")
          ) {
            isReconnectionRef.current = true;
            shouldSendBrowserReadyRef.current = false;
            toast.success("Reconnected to existing Blender session");
          }
          break;

        case MessageType.BLENDER_DISCONNECTED: {
          const disconnectReason = isResponsePayload(payload)
            ? payload.data?.reason ?? ""
            : "";
          const isTransportDrop = disconnectReason === "transport close";

          if (isTransportDrop) {
            // Network blip — Blender client will auto-reconnect in ~2s.
            // Keep scene data intact, disable controls, show subtle indicator.
            setBlenderConnected(false);
            setConnectionState("blender_reconnecting");

            // Clear any timer from a PRIOR drop episode before scheduling this
            // one's — without this, a flappy connection (a second "transport
            // close" arriving before the first episode's timer fires or gets
            // cleared) orphans the earlier timer instead of cancelling it. An
            // orphaned timer keeps running detached from the ref and can fire
            // its "Blender disconnected" toast during a LATER, unrelated
            // blender_reconnecting window — which is what made the toast
            // appear to lag behind (or outlive) the actual disconnect.
            if (blenderReconnectTimerRef.current) {
              clearTimeout(blenderReconnectTimerRef.current);
            }

            // Escalate to full disconnect after 15s if Blender doesn't come back
            blenderReconnectTimerRef.current = setTimeout(() => {
              blenderReconnectTimerRef.current = null;
              setConnectionState((prev) => {
                if (prev !== "blender_reconnecting") return prev;
                // Now it's a real disconnect — flush scene data
                queryClient.setQueryData(sceneContextKeys.objects(), null);
                setContextUpdateSent(false);
                toast.info("Blender disconnected");
                return "blender_disconnected";
              });
            }, 15_000);
          } else {
            // Intentional disconnect or crash — show full disconnect UI immediately
            useLaunchTimerStore.getState().stop();
            setBlenderConnected(false);
            setConnectionState("blender_disconnected");
            queryClient.setQueryData(sceneContextKeys.objects(), null);
            setContextUpdateSent(false);
            if (isResponsePayload(payload)) {
              toast.info(payload.data?.message || "Blender disconnected");
            }
          }
          break;
        }

        case MessageType.INBOX_CLEARED:
          useInboxStore.getState().clearAll();
          toast.success("Inbox cleared successfully");
          break;

        case MessageType.COMMAND_COMPLETED:
          // Handle scene context updates from list_scene_objects command
          if (isResponsePayload(payload) && payload.status === "success") {
            // Check if this is a scene objects response (array of objects nested in data.data)
            const hasData = payload.data?.data;
            const isArray = Array.isArray(payload.data?.data);
            const hasLength = payload.data?.data?.length > 0;
            const hasFirstName = payload.data?.data?.[0]?.name;

            if (hasData && isArray && hasLength && hasFirstName) {
              // Scenario A: response IS scene data — update cache directly, no refetch
              queryClient.setQueryData(sceneContextKeys.objects(), {
                objects: payload.data.data,
                timestamp: Math.floor(Date.now() / 1000),
              });
            }
            // Scenario B: non-scene commands (transforms, viewport changes, etc.)
            // — do NOT invalidate. The 2-second polling handles scene sync.
            // Calling invalidateQueries here caused burst-firing of list_scene_objects
            // after every command, overwhelming the Blender socket.io client.
            // Remove toast.success completely - direct commands have visual feedback
            // Only agent commands should send success responses if needed
          }
          break;

        case MessageType.COMMAND_FAILED:
          if (isResponsePayload(payload) && payload.error) {
            toast.error(payload.error.user_message);
            console.error("Command failed:", payload.error.technical_message);
          }
          break;

        case MessageType.AGENT_PROCESSING:
          // Mid-run progress. Goes to the activity feed only — no toast, or a
          // tool-heavy request would bury the screen in notifications.
          {
            const activity = payload as SystemPayload;
            if (activity?.message) {
              useBlazeChatStore
                .getState()
                .addActivity(activity.status ?? "activity", activity.message);
            }
          }
          break;

        case MessageType.SCENE_CONTEXT_UPDATED:
          // Blender telling us what it actually is, rather than what the UI
          // optimistically assumed. Currently carries viewport shading, which
          // B.L.A.Z.E changes on its own before taking a screenshot.
          {
            const update = payload as SystemPayload;
            const mode = update?.data?.viewport_mode;
            if (mode === "solid" || mode === "rendered") {
              useNavigationStore.getState().setViewportMode(mode);
            }
          }
          break;

        case MessageType.AGENT_RESPONSE_READY:
          if (isResponsePayload(payload) && payload.data?.message) {
            // No toast: the chat panel is the transcript now, and the Blaze mark
            // in the bottom controls already signals a finished turn. Toasting a
            // full reply on top of that just covers the viewport.
            useBlazeChatStore.getState().addAssistant(payload.data.message);
          }
          // The turn is over whether or not it carried a message, so the
          // activity indicator must stop pulsing either way.
          useBlazeChatStore.getState().setBusy(false);
          // A finished turn has usually changed the scene — imported assets,
          // moved things. The 5s poll makes that feel laggy, so refresh now.
          // This is one refetch per turn, not per command: invalidating on every
          // COMMAND_COMPLETED is what previously flooded the Blender socket.
          queryClient.invalidateQueries({
            queryKey: sceneContextKeys.objects(),
          });
          break;

        case MessageType.AGENT_ERROR:
          if (isResponsePayload(payload) && payload.error) {
            useBlazeChatStore.getState().addError(payload.error.user_message);
            // Unlike a successful reply, a failure is worth interrupting for —
            // but only if the user isn't already looking at the chat, where the
            // error appears in red anyway.
            {
              const vis = useVisibilityStore.getState();
              const chatOnScreen =
                vis.isAssetSelectionVisible && vis.rightPanel === "chat";
              if (!chatOnScreen) {
                toast.error("B.L.A.Z.E: " + payload.error.user_message);
              }
            }
            console.error("Agent error:", payload.error.technical_message);
            if (payload.error.recovery_suggestions?.length) {
              console.info(
                "Recovery suggestions:",
                payload.error.recovery_suggestions
              );
            }
          }
          useBlazeChatStore.getState().setBusy(false);
          break;

        case MessageType.EXECUTION_ERROR:
          if (isResponsePayload(payload) && payload.error) {
            toast.error(payload.error.user_message);
            console.error("Execution error:", payload.error.technical_message);
          }
          break;

        default:
          console.log("Unhandled message type:", message.type);
      }

      // Forward to custom handler
      onMessage?.(data);
    },
    [onMessage]
  );

  // Define cleanup callback for when server is unavailable for 5+ minutes
  const performServerCleanup = useCallback(() => {
    console.log("Performing cleanup after 5 minutes of server downtime");

    // Clear application state
    useLaunchTimerStore.getState().stop();
    queryClient.setQueryData(sceneContextKeys.objects(), null);
    useInboxStore.getState().clearAll();

    // Update connection state
    setBlenderConnected(false);
    setConnectionState("server_unavailable");
    setContextUpdateSent(false);
    setSessionCreated(false);

    // Notify user
    toast.error("Server unavailable for 5+ minutes. Session cleared.", {
      duration: 10000,
    });
  }, [queryClient]);

  const wsHook = useSocketIO(remoteUser, (data: any) => {
    // Process message first
    processMessage(data);

    // Handle session creation (Socket.IO connect event)
    if (data.type === "system" && data.status === "connected") {
      toast.success("Connected to Cr8 Engine");
      setSessionCreated(true);
      setConnectionState("browser_connected");
      // Only prepare to send browser_ready for fresh connections
      if (!isReconnectionRef.current) {
        shouldSendBrowserReadyRef.current = true;
      }
    }
  }, performServerCleanup);

  // Check server health endpoint via server function to avoid CORS
  const checkServerHealth = useCallback(async (): Promise<boolean> => {
    try {
      const { healthy } = await checkEngineHealthFn();
      return healthy;
    } catch (error) {
      console.error("Health check failed:", error);
      return false;
    }
  }, []);

  // Hybrid reconnect: handles both Blender relaunch and full server reconnection
  const reconnect = useCallback(async () => {
    // If socket is connected but Blender is not, send browser_ready signal to relaunch Blender
    if (
      wsHook.socket?.connected &&
      (connectionState === "blender_disconnected" || connectionState === "blender_reconnecting")
    ) {
      setConnectionState("reconnecting");
      console.log("Sending browser_ready signal to relaunch Blender");
      wsHook.socket.emit("browser_ready", { recovery: true });
    } else if (
      connectionState === "server_unavailable" ||
      connectionState === "disconnected" ||
      connectionState === "connecting"
    ) {
      // Check if server is back online before attempting reconnect (for both server_unavailable and disconnected states)
      console.log(`Server was ${connectionState}, checking health endpoint...`);
      setIsHealthCheckInProgress(true);
      try {
        const isHealthy = await checkServerHealth();
        if (!isHealthy) {
          toast.error("Server still unavailable");
          return;
        }
        // Server is healthy, proceed with reconnect
        console.log("Server is healthy, attempting reconnect");
        wsHook.reconnect();
      } finally {
        setIsHealthCheckInProgress(false);
      }
    } else {
      // Otherwise, do full reconnect cycle (for general disconnection)
      console.log("Performing full reconnect cycle");
      wsHook.reconnect();
    }
  }, [wsHook.socket, wsHook.reconnect, connectionState, checkServerHealth]);

  // Send browser_ready for fresh connections only
  useEffect(() => {
    if (
      sessionCreated &&
      shouldSendBrowserReadyRef.current &&
      wsHook.socket?.connected &&
      !isReconnectionRef.current
    ) {
      const timeoutId = setTimeout(() => {
        console.log("Sending browser_ready signal for fresh connection");
        wsHook.sendMessage({ command: "browser_ready" });
        shouldSendBrowserReadyRef.current = false;
      }, 100);

      return () => clearTimeout(timeoutId);
    }
  }, [sessionCreated, wsHook.socket, wsHook.sendMessage]);

  // Handle context updates for both fresh and reconnected sessions
  useEffect(() => {
    if (
      wsHook.isConnected &&
      blenderConnected &&
      !contextUpdateSent &&
      wsHook.socket?.connected
    ) {
      const messageId = isReconnectionRef.current
        ? `reconnect_context_update_${Date.now()}`
        : `context_update_${Date.now()}`;

      console.log(
        isReconnectionRef.current
          ? "Browser reconnected, sending context update request"
          : "Sending initial context update request"
      );

      wsHook.socket?.emit("command_sent", {
        message_id: messageId,
        type: "command_sent",
        payload: {
          addon_id: ADDON_IDS.SETS,
          command: "list_scene_objects",
          params: {},
        },
        metadata: {
          route: "direct",
          source: "browser",
        },
      });

      setContextUpdateSent(true);
    }
  }, [
    wsHook.isConnected,
    blenderConnected,
    contextUpdateSent,
    wsHook.socket,
    wsHook.sendMessage,
  ]);

  // Stop the launch timer and reconnect grace timer when the workspace unmounts.
  useEffect(() => {
    return () => {
      useLaunchTimerStore.getState().stop();
      if (blenderReconnectTimerRef.current) {
        clearTimeout(blenderReconnectTimerRef.current);
        blenderReconnectTimerRef.current = null;
      }
    };
  }, []);

  // Handle logout disconnection
  useEffect(() => {
    const handleLogoutDisconnect = () => {
      console.log("Logout event received, disconnecting Socket.IO");
      if (blenderReconnectTimerRef.current) {
        clearTimeout(blenderReconnectTimerRef.current);
        blenderReconnectTimerRef.current = null;
      }
      if (wsHook.socket) {
        wsHook.disconnect();
        setBlenderConnected(false);
        setContextUpdateSent(false);
        setSessionCreated(false);
        setConnectionState("disconnected");
        isReconnectionRef.current = false;
        shouldSendBrowserReadyRef.current = false;
      }
    };

    window.addEventListener("logout-disconnect", handleLogoutDisconnect);
    return () =>
      window.removeEventListener("logout-disconnect", handleLogoutDisconnect);
  }, [wsHook.socket, wsHook.disconnect]);

  // Handle initial connection failure
  useEffect(() => {
    // Only show toast for initial connection failures (not reconnections).
    // wsHook.status === "failed" is the signal that the attempt is genuinely
    // over, so the still-in-flight "connecting" state counts here too.
    if (
      wsHook.status === "failed" &&
      (connectionState === "disconnected" || connectionState === "connecting") &&
      !isReconnectionRef.current
    ) {
      // The first attempt has now definitively failed, so stop presenting it as
      // in-progress — this is what flips the UI to its reconnect affordance.
      setConnectionState("disconnected");
      console.log("Initial connection failed, checking server health...");
      checkServerHealth().then((isHealthy) => {
        if (!isHealthy) {
          toast.error(
            "Cannot connect to server - Please check if Cr8 Engine is running"
          );
        }
      });
    }
  }, [wsHook.status, connectionState, checkServerHealth]);

  const cancelLaunch = useCallback(() => {
    if (wsHook.socket?.connected) {
      wsHook.socket.emit("cancel_launch");
      setInstanceStatus({
        phase: "cancelled",
        elapsed: instanceStatus?.elapsed ?? 0,
      });
    }
  }, [wsHook.socket, instanceStatus]);

  const saveFile = useCallback(
    (filename?: string): Promise<boolean> => {
      const socket = wsHook.socket;
      if (!socket?.connected) {
        toast.error("Not connected — can't save right now");
        return Promise.resolve(false);
      }
      setIsSaving(true);
      const p = new Promise<boolean>((resolve) => {
        const messageId = `save_${Date.now()}_${Math.random()
          .toString(36)
          .slice(2)}`;
        pendingSavesRef.current.set(messageId, resolve);
        socket.emit("save_file", {
          message_id: messageId,
          filename: filename?.trim() || undefined,
        });
        // Safety net for a genuinely lost response (e.g. the socket died). Set
        // well above the backend's own save ceiling (~20 min for a large
        // multipart upload) so a slow-but-working save resolves normally first.
        setTimeout(() => {
          if (pendingSavesRef.current.has(messageId)) {
            pendingSavesRef.current.delete(messageId);
            toast.error("Save timed out");
            resolve(false);
          }
        }, 25 * 60_000);
      });
      // A Save As that landed means the session now has a cloud target, so
      // later plain Saves — and Exit — must stop asking for a name.
      if (filename?.trim()) p.then((ok) => ok && setSavedAs(true));
      // Clear the blocking overlay whichever way the save settles.
      p.finally(() => setIsSaving(false));
      return p;
    },
    [wsHook.socket]
  );

  const renderImage = useCallback(
    (options: RenderOptions): Promise<RenderResult> => {
      const socket = wsHook.socket;
      if (!socket?.connected) {
        toast.error("Not connected — can't render right now");
        return Promise.resolve({ ok: false, message: "Not connected" });
      }
      setIsRendering(true);
      const p = new Promise<RenderResult>((resolve) => {
        const messageId = `render_${Date.now()}_${Math.random()
          .toString(36)
          .slice(2)}`;
        pendingRendersRef.current.set(messageId, resolve);
        socket.emit("render_image", {
          message_id: messageId,
          camera: options.camera || undefined,
          engine: options.engine,
          resolution: options.resolution,
          aspect: options.aspect,
        });
        // Safety net for a genuinely lost response. Set above the backend's own
        // RENDER_TIMEOUT_SECONDS (30 min) so a slow-but-working Cycles render
        // always resolves on its own first.
        setTimeout(() => {
          if (pendingRendersRef.current.has(messageId)) {
            pendingRendersRef.current.delete(messageId);
            toast.error("Render timed out");
            resolve({ ok: false, message: "Render timed out" });
          }
        }, 35 * 60_000);
      });
      p.finally(() => setIsRendering(false));
      return p;
    },
    [wsHook.socket]
  );

  const exitWorkspace = useCallback(() => {
    if (wsHook.socket?.connected) {
      wsHook.socket.emit("exit_workspace");
    }
  }, [wsHook.socket]);

  const contextValue = {
    ...wsHook,
    blenderConnected,
    blenderConnectedOnce,
    isFullyConnected: wsHook.isConnected && blenderConnected,
    connectionState,
    isHealthCheckInProgress,
    instanceStatus,
    cancelLaunch,
    reconnect,
    saveFile,
    isSaving,
    hasCloudTarget: !!selectedBlendObjectKey || savedAs,
    renderImage,
    isRendering,
    exitWorkspace,
  };

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error(
      "useWebSocketContext must be used within a WebSocketProvider"
    );
  }
  return context;
}
