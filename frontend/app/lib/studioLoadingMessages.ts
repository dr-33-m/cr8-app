/**
 * Loading messages for the studio launch sequence.
 * Keyed to VastAI instance status phases, written for creative professionals
 * who care about storytelling — not infrastructure.
 */

export const STUDIO_MESSAGES: Record<string, string[]> = {
  created: [
    "Your studio is being prepared...",
    "We found you the perfect space.",
    "Securing your creative suite. One moment.",
  ],
  provisioning: [
    "Reserving your private studio...",
    "Getting the keys to your space.",
    "Your studio is being assigned. Almost in.",
  ],
  loading: [
    "Bringing in the furniture...",
    "Hanging the lights and setting the mood.",
    "Loading your creative environment.",
    "Carrying in the props. Heavy ones first.",
    "Dressing the set. Making it yours.",
    "Your studio is taking shape — sit tight.",
    "Setting up the stage for your vision.",
    "Assembling the scene. Nearly there.",
    "Rolling in the equipment. Worth the wait.",
    "The crew is getting everything ready for you.",
  ],
  running: [
    "Studio ready! Opening the doors...",
    "The lights are on. Stepping inside...",
    "Your world is ready — connecting now.",
    "Everything's set. Walking you in...",
  ],
  blender_connected: [
    "Your studio is ready — connecting the camera...",
    "Almost there — establishing the video feed.",
    "Final step — streaming your viewport.",
  ],
  // Post-VastAI phases: SSH + Blender launch pipeline
  ssh_key_attaching: [
    "Handing over the keys...",
    "Setting up secure access to your studio.",
  ],
  ssh_connecting: [
    "Opening the studio door...",
    "Connecting to your creative space.",
    "Establishing a secure link to your GPU.",
  ],
  blender_starting: [
    "Warming up the render engine...",
    "Firing up Blender on your GPU.",
    "Starting your creative tools.",
  ],
  "blender:env_setup": [
    "Setting up the environment...",
    "Preparing the workspace internals.",
  ],
  "blender:nvidia_driver": [
    "Installing GPU drivers...",
    "Tuning the graphics hardware.",
    "Configuring the GPU. This may take a moment.",
  ],
  "blender:xorg_setup": [
    "Setting up the display server...",
    "Configuring the virtual display.",
  ],
  "blender:gst_preflight": [
    "Running streaming preflight checks...",
    "Preparing the video pipeline.",
  ],
  "blender:blender_launching": [
    "Blender is starting up...",
    "Almost there — launching your canvas.",
    "Your studio is opening. Final moments.",
  ],
  retrying: [
    "Trying a different GPU...",
    "That studio wasn't quite right. Finding another.",
    "Switching to a new machine. Hang tight.",
  ],
  error: [
    "Something went wrong setting up your studio.",
    "We hit a bump. Let's try again.",
  ],
  cancelled: [
    "Launch cancelled.",
  ],
  default: [
    "Preparing your creative space...",
    "Getting your studio ready.",
    "Setting the scene for you.",
  ],
};

/** User-friendly error messages by failure reason. */
export const ERROR_REASONS: Record<string, string> = {
  timeout: "Your studio took too long to set up. The GPU might be busy.",
  ssh_failed: "Couldn't connect to your studio. The connection dropped.",
  blender_failed: "Blender failed to start on the GPU instance.",
  no_gpu: "No GPUs available right now. Try again in a few minutes.",
  local_failed: "Blender failed to start locally. Check your setup.",
  unknown: "Something unexpected happened. Please try again.",
};

export function getStudioMessages(phase: string): string[] {
  if (STUDIO_MESSAGES[phase]) return STUDIO_MESSAGES[phase];
  // Unmapped blender sub-phases (e.g. "blender:nvidia_cached:550") fall back to blender_starting
  if (phase.startsWith("blender:")) return STUDIO_MESSAGES.blender_starting;
  return STUDIO_MESSAGES.default;
}

export function formatElapsed(elapsed: number): string {
  if (elapsed < 60) return `${elapsed}s`;
  return `${Math.floor(elapsed / 60)}m ${elapsed % 60}s`;
}
