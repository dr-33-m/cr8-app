import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import {
  ChevronDown,
  ChevronUp,
  SendHorizontal,
  Play,
  Pause,
  SkipBack,
  SkipForward,
  StepBack,
  StepForward,
  Eye,
  Monitor,
  Plus,
  Minus,
  ArrowUp,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  RotateCcw,
} from "lucide-react";
import { useVisibilityStore } from "@/store/controlsVisibilityStore";
import { useWebSocketContext } from "@/contexts/WebSocketContext";
import { ConnectionStatus } from "./ConnectionStatus";
import { useState, useRef, useEffect } from "react";
import { toast } from "sonner";

interface BottomControlsProps {
  children?: React.ReactNode;
}

export function BottomControls({ children }: BottomControlsProps) {
  const [message, setMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [animationState, setAnimationState] = useState<
    "playing" | "paused" | "playing_reverse"
  >("paused");
  const [viewportMode, setViewportMode] = useState<"solid" | "rendered">(
    "solid"
  );
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const isVisible = useVisibilityStore(
    (state) => state.isBottomControlsVisible
  );
  const onToggleVisibility = useVisibilityStore(
    (state) => state.toggleBottomControls
  );

  // Get WebSocket context directly - this component is now only used within WebSocketProvider
  const { status, reconnect, sendMessage, isFullyConnected } =
    useWebSocketContext();

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height =
        textareaRef.current.scrollHeight + "px";
    }
  }, [message]);

  const handleSendMessage = async () => {
    if (!message.trim() || !isFullyConnected || isLoading) return;

    setIsLoading(true);
    try {
      // Send message to B.L.A.Z.E Agent
      sendMessage({
        type: "agent_message",
        message: message.trim(),
      });

      // Clear input
      setMessage("");
      toast.success("Message sent to B.L.A.Z.E");
    } catch (error) {
      toast.error("Failed to send message");
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Navigation command functions
  const sendNavigationCommand = async (command: string) => {
    if (!isFullyConnected) return;

    try {
      sendMessage({
        type: "addon_command",
        addon_id: "blender_ai_router",
        command: command,
        params: {},
      });
    } catch (error) {
      toast.error(`Failed to send ${command} command`);
    }
  };

  // Animation controls
  const handleFrameJumpStart = () => sendNavigationCommand("frame_jump_start");
  const handleFrameJumpEnd = () => sendNavigationCommand("frame_jump_end");
  const handleKeyframeJumpPrev = () =>
    sendNavigationCommand("keyframe_jump_prev");
  const handleKeyframeJumpNext = () =>
    sendNavigationCommand("keyframe_jump_next");

  const handleAnimationPlay = () => {
    if (animationState === "playing") {
      sendNavigationCommand("animation_pause");
      setAnimationState("paused");
    } else {
      sendNavigationCommand("animation_play");
      setAnimationState("playing");
    }
  };

  const handleAnimationPlayReverse = () => {
    sendNavigationCommand("animation_play_reverse");
    setAnimationState("playing_reverse");
  };

  // Viewport controls
  const handleViewportSolid = () => {
    if (viewportMode !== "solid") {
      sendNavigationCommand("viewport_set_solid");
      setViewportMode("solid");
    }
  };

  const handleViewportRendered = () => {
    if (viewportMode !== "rendered") {
      sendNavigationCommand("viewport_set_rendered");
      setViewportMode("rendered");
    }
  };

  // 3D Navigation controls
  const handleZoomIn = () => sendNavigationCommand("zoom_in");
  const handleZoomOut = () => sendNavigationCommand("zoom_out");
  const handlePanUp = () => sendNavigationCommand("pan_up");
  const handlePanDown = () => sendNavigationCommand("pan_down");
  const handlePanLeft = () => sendNavigationCommand("pan_left");
  const handlePanRight = () => sendNavigationCommand("pan_right");
  const handleOrbitLeft = () => sendNavigationCommand("orbit_left");
  const handleOrbitRight = () => sendNavigationCommand("orbit_right");
  const handleOrbitUp = () => sendNavigationCommand("orbit_up");
  const handleOrbitDown = () => sendNavigationCommand("orbit_down");

  return (
    <div
      className={`absolute bottom-4 left-1/2 transform -translate-x-1/2 transition-all duration-300 
      ${isVisible ? "translate-y-0" : "translate-y-full"}`}
    >
      <Button
        variant="ghost"
        size="icon"
        className="absolute left-1/2 -top-12 -translate-x-1/2 text-white hover:bg-white/10"
        onClick={onToggleVisibility}
      >
        {isVisible ? (
          <ChevronDown className="h-6 w-6" />
        ) : (
          <ChevronUp className="h-6 w-6" />
        )}
      </Button>
      <div className="backdrop-blur-md bg-white/5 rounded-lg p-4 grid grid-cols-[auto_1fr_auto] grid-rows-[auto_auto_auto] gap-4 min-w-[500px]">
        {status === "disconnected" ? (
          <div className="col-span-3 row-span-3 flex items-center justify-center">
            <Button
              variant="secondary"
              onClick={reconnect}
              className="bg-blue-500 hover:bg-blue-600 text-white"
            >
              Reconnect
            </Button>
          </div>
        ) : isFullyConnected ? (
          <>
            {/* Row 1 Left: Viewport Controls */}
            <div className="flex items-center gap-2">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleViewportSolid}
                className={`px-3 py-2 text-xs backdrop-blur-md border transition-all duration-200 ${
                  viewportMode === "solid"
                    ? "bg-primary/30 border-primary/80"
                    : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
                }`}
              >
                <Eye className="h-3 w-3 mr-1" />
                Solid
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleViewportRendered}
                className={`px-3 py-2 text-xs backdrop-blur-md border transition-all duration-200 ${
                  viewportMode === "rendered"
                    ? "bg-primary/30 border-primary/80"
                    : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10"
                }`}
              >
                <Monitor className="h-3 w-3 mr-1" />
                Rendered
              </Button>
            </div>

            {/* Row 1 Center: Empty */}
            <div></div>

            {/* Row 1 Right: Connection Status */}
            <div className="flex items-center justify-end">
              <ConnectionStatus status={status} />
            </div>

            {/* Row 2: Chat Interface (Auto-growing) - Spans all 3 columns */}
            <div className="relative flex justify-center col-span-3">
              <Textarea
                ref={textareaRef}
                placeholder="Tell B.L.A.Z.E what to do..."
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyPress={handleKeyPress}
                className="w-full min-h-[40px] max-h-[120px] resize-none pr-10 bg-cr8-charcoal/10 border-white/10 backdrop-blur-md shadow-lg text-white placeholder:text-white/60 overflow-hidden"
                disabled={isLoading}
              />
              <SendHorizontal
                onClick={handleSendMessage}
                className={`absolute right-3 top-3 h-4 w-4 cursor-pointer transition-colors duration-200 ${
                  !message.trim() || isLoading
                    ? "text-gray-500 cursor-not-allowed"
                    : "text-blue-400 hover:text-blue-300"
                }`}
              />
            </div>

            {/* Row 3: Animation Controls - Spans all 3 columns */}
            <div className="flex items-center justify-center gap-1 col-span-3">
              <Button
                variant="ghost"
                size="sm"
                onClick={handleFrameJumpStart}
                className="p-2 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
                title="Jump to start"
              >
                <SkipBack className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleKeyframeJumpPrev}
                className="p-2 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
                title="Previous keyframe"
              >
                <StepBack className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleAnimationPlay}
                className={`p-2 border transition-all duration-200 ${
                  animationState === "playing"
                    ? "bg-green-500/20 border-green-400/40 text-green-300"
                    : "bg-white/5 border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
                }`}
                title={animationState === "playing" ? "Pause" : "Play"}
              >
                {animationState === "playing" ? (
                  <Pause className="h-3 w-3" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleKeyframeJumpNext}
                className="p-2 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
                title="Next keyframe"
              >
                <StepForward className="h-3 w-3" />
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={handleFrameJumpEnd}
                className="p-2 bg-white/5 border border-white/10 text-white/70 hover:bg-white/10 hover:text-white"
                title="Jump to end"
              >
                <SkipForward className="h-3 w-3" />
              </Button>
            </div>
          </>
        ) : (
          <div className="col-span-3 row-span-3 flex items-center justify-center text-white/60 text-sm">
            Waiting for Blender connection...
          </div>
        )}
      </div>

      {/* Separate 3D Navigation Panel - Positioned to the right */}
      {isFullyConnected && (
        <div
          className={`absolute bottom-0 left-[calc(50%+280px)] transition-all duration-300 
    ${isVisible ? "translate-y-0" : "translate-y-full"}`}
        >
          <div className="backdrop-blur-md bg-white/5 rounded-lg p-3 border border-white/10">
            <div className="flex flex-col gap-3">
              {/* Top Row - Zoom In and Pan Up */}
              <div className="flex justify-center gap-3">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleZoomIn}
                  className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
                  title="Zoom In"
                >
                  <Plus className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handlePanUp}
                  className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
                  title="Pan Up"
                >
                  <ArrowUp className="h-4 w-4" />
                </Button>
              </div>

              {/* Middle Row - Pan Left, Center Space, Pan Right */}
              <div className="flex justify-center items-center gap-3">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handlePanLeft}
                  className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
                  title="Pan Left"
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <div className="w-10 h-10"></div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handlePanRight}
                  className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
                  title="Pan Right"
                >
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>

              {/* Bottom Row - Zoom Out, Pan Down, and Orbit Control */}
              <div className="flex justify-center items-center gap-3">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handleZoomOut}
                  className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
                  title="Zoom Out"
                >
                  <Minus className="h-4 w-4" />
                </Button>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={handlePanDown}
                  className="w-10 h-10 bg-black/40 border border-white/20 text-white hover:bg-white/10 rounded-lg"
                  title="Pan Down"
                >
                  <ArrowDown className="h-4 w-4" />
                </Button>

                {/* Orbit Control Wheel */}
                <div className="w-16 h-16 relative flex items-center justify-center">
                  <div className="w-16 h-16 bg-black/40 border border-white/20 rounded-full relative overflow-hidden">
                    {/* Top Quarter - Orbit Up */}
                    <button
                      onClick={handleOrbitUp}
                      className="absolute top-0 left-1/2 transform -translate-x-1/2 w-8 h-8 hover:bg-white/20 rounded-t-full transition-colors flex items-center justify-center"
                      title="Orbit Up"
                    >
                      <ArrowUp className="h-4 w-4 text-white/90" />
                    </button>

                    {/* Right Quarter - Orbit Right */}
                    <button
                      onClick={handleOrbitRight}
                      className="absolute right-0 top-1/2 transform -translate-y-1/2 w-8 h-8 hover:bg-white/20 rounded-r-full transition-colors flex items-center justify-center"
                      title="Orbit Right"
                    >
                      <ArrowRight className="h-4 w-4 text-white/90" />
                    </button>

                    {/* Bottom Quarter - Orbit Down */}
                    <button
                      onClick={handleOrbitDown}
                      className="absolute bottom-0 left-1/2 transform -translate-x-1/2 w-8 h-8 hover:bg-white/20 rounded-b-full transition-colors flex items-center justify-center"
                      title="Orbit Down"
                    >
                      <ArrowDown className="h-4 w-4 text-white/90" />
                    </button>

                    {/* Left Quarter - Orbit Left */}
                    <button
                      onClick={handleOrbitLeft}
                      className="absolute left-0 top-1/2 transform -translate-y-1/2 w-8 h-8 hover:bg-white/20 rounded-l-full transition-colors flex items-center justify-center"
                      title="Orbit Left"
                    >
                      <ArrowLeft className="h-4 w-4 text-white/90" />
                    </button>

                    {/* Center Circle */}
                    <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-6 h-6 bg-white/20 rounded-full"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
