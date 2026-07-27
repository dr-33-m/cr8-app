/**
 * Blender addon identifiers.
 *
 * Every command the browser sends carries an `addon_id` naming which Blender
 * addon should handle it. These strings are a contract with three other places,
 * and all four must agree exactly:
 *
 *   1. `id` in the addon's `blender_manifest.toml`  (the Blender extension id)
 *   2. `addon_info.id` in the addon's `addon_ai.json` (what the router registers)
 *   3. the addon's source directory name under `backend/`
 *   4. this file
 *
 * They were previously spelled differently in each place — cr8_sets answered to
 * `multi_registry_assets`, cr8_router to `blender_ai_router` — and the literals
 * were copy-pasted across seven files, so a rename meant finding every one of
 * them. Import from here instead of typing the string.
 *
 * A wrong id fails at runtime, not at build time: the router replies
 * NO_HANDLERS and the command silently does nothing.
 */
export const ADDON_IDS = {
  /** WebSocket/WebRTC transport and command routing. Default for direct commands. */
  ROUTER: "cr8_router",
  /** Asset registries (Polyhaven) and scene spatial ops — transforms, selection. */
  SETS: "cr8_sets",
  /** Animation, viewport and navigation controls. */
  CONTROLS: "cr8_controls",
  /** Python execution fallback for the agent. */
  SCRIPT: "cr8_script",
  /** Rendering and cloud output. */
  RENDER: "cr8_render",
} as const;

export type AddonId = (typeof ADDON_IDS)[keyof typeof ADDON_IDS];
