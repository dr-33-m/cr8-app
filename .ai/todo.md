# Make the viewport stream feed immediately on connect

Plan: `~/.claude/plans/this-one-is-a-polished-quokka.md`

Symptom: after connecting to an instance the viewport stays black until the user
orbits the camera several times.

## Part A — cr8_router redraw pump

- [x] `ws/handlers/event_handlers.py` — module-level `_redraw_pump` timer at stream fps
- [x] `_ensure_redraw_pump` / `_stop_redraw_pump` helpers
- [x] Register on both `start_streaming_if_needed` paths (fresh start *and* the
      already-active reconnect path)
- [x] Unregister on intentional disconnect only, alongside `streaming.stop()`
- [x] Replace the old one-shot `_force_initial_redraw`
- [x] `_STREAM_WIDTH/HEIGHT/FPS` constants so the pump interval and
      `streaming.configure()` cannot drift apart
- [x] Suppress repeat warnings so a persistent fault logs once, not 30×/s

## Part B — Blender fork timestamps

- [x] `streaming_gstreamer.cc` — drop manual `GST_BUFFER_PTS` in
      `streaming_send_composited_texture()`
- [x] Same in `streaming_send_test_pattern()`
- [x] Remove dead `timestamp` field (`streaming_intern.h`) + its two initialisations

## Part C — Frontend watchdog

- [x] `useWebRTCStream.ts` — 15s connect watchdog, 3-attempt retry with producer
      re-resolution
- [x] Bound the `rtcPeerConnection` poll (was unbounded 100ms forever)
- [x] Close the leaked session on `producerRemoved`
- [x] Cancel both timers in effect cleanup
- [x] **(found during implementation)** `applyConnected`/`applyConnecting` write ref
      and state together

## Review

**Root cause.** Frames exist only as a side effect of the viewport drawing —
`BKE_streaming_send_viewport_frame()` is called from `view3d_draw.cc:1778` and
`wm_draw.cc:1049`, both gated on `region->runtime->do_draw`. An instance with nobody
at the keyboard tags no redraws, so zero buffers reach `appsrc` and `webrtcsink` has
nothing to encode. Orbiting the camera *was* the frame pump.

**Second defect, found while reading the pipeline.** `appsrc` runs with
`do-timestamp=TRUE` while the code also hand-wrote `PTS = n × (1/fps)`.
`gstbasesrc.c:2398-2430` only fills in a timestamp it finds *invalid*, so the manual
PTS survived and DTS (running time) diverged from it by the accumulated idle time.
Fixing only the pump would have made the stream start and then fall progressively
further behind, since the capture path cannot sustain 30fps through an 8.3MB readback
plus a 2M-pixel scalar conversion.

**Design decisions:**

1. *Pump in Python, not C++.* The streaming feature lives in the fork, but a C-side
   pump would need the streaming module (blenkernel-adjacent) to reach into the window
   manager, inverting Blender's module dependency direction. The addon layer already
   owns streaming start/stop and knows the configured fps, and ships without a rebuild.

2. *Pump ticks at exactly 1/fps, not faster.* `streaming_should_send_frame()` gates
   *after* the viewport has already redrawn, so an over-eager pump pays full render
   cost for frames it then discards.

3. *No idle backoff*, deliberately breaking the convention `_drain_command_queue`
   follows. Idle is exactly when the stream would stall. Bounded instead by only
   running while `streaming.is_active()`.

4. *Repointed OptiX rather than disabling it.* The fork's build tree pointed at
   NVIDIA-OptiX-SDK-**8.0.0**, which no longer exists (8.1.0 is installed). Unrelated
   pre-existing breakage; repointing keeps Cycles' OptiX device rather than silently
   dropping it from the next production build.

**Verification.** bpy surface checked against the real build
(`Region.tag_redraw`, `Region.type` enum incl. `WINDOW`, `Area.regions`,
`bpy.app.streaming.is_active`, `timers.register(first_interval=0.0)`) — the repo's own
lesson says never to infer a bpy API from prose.

Viewport redraw rate measured directly with a `SpaceView3D` draw-handler counter over
4s, GUI Blender on a real display, repeated on an idle machine:

| | draws | fps |
|---|---|---|
| no pump | 8 (all startup) | 2.0 |
| pump | 109 | 27.2 |

Fork rebuilt clean (`BUILD_EXIT=0`, zero errors) and the new binary still reports
`Streaming system initialized`; `bpy.app.streaming.configure(...)` accepts the addon's
full arg set after the `StreamingContext` field removal. Frontend typechecks clean.

**Confirmed working on a live instance** (2026-07-28): the stream feeds as soon as the
browser attaches, with no viewport interaction.

**Known caveats.** The pump delivers ~27fps, not 30 — `bpy.app.timers` schedule the
next call *after* the callback returns, so a 33.3ms interval becomes ~36.7ms. Harmless
now that timestamps follow the real clock, but it is exactly the case that would have
drifted ~10% (6s of lag per minute) under the old hand-written PTS. Ticking faster to
chase 30 would start losing renders to `streaming_should_send_frame()`, so it is left
alone.

The per-pixel float→uint8 loop
(`streaming_gstreamer.cc:515-535`) is the real framerate ceiling; if 30fps proves
unreachable the cheap lever is dropping `_STREAM_WIDTH/HEIGHT` to 1280×720 (2.25× less
work per frame). The pump renders whenever streaming is active, even if no browser is
attached — gating on `webrtcsink`'s `consumer-added`/`consumer-removed` would fix that
but needs a new C-side API plus an engine→Blender message.
