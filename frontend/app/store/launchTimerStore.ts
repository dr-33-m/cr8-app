import { create } from "zustand";

interface LaunchTimerState {
  elapsed: number;
  // Seconds since the last phase change — divide by 4 and mod messages.length to get msgIndex.
  msgTick: number;
  // Call on every INSTANCE_STATUS update. Anchors the wall-clock reference once per session
  // and resets msgTick when the phase changes so messages restart from index 0.
  seed: (backendElapsed: number, phase: string) => void;
  // Call when the timer should stop (Blender connected, disconnect, server cleanup).
  stop: () => void;
}

// Module-level — lives outside Zustand to avoid closure stale-ref issues.
let _intervalId: ReturnType<typeof setInterval> | null = null;
let _startAt: number | null = null;
let _msgTick = 0;
let _currentPhase: string | null = null;

export const useLaunchTimerStore = create<LaunchTimerState>((set) => ({
  elapsed: 0,
  msgTick: 0,

  seed: (backendElapsed: number, phase: string) => {
    // Anchor wall-clock reference once — prevents counter jumping on polling updates.
    if (_startAt === null) {
      _startAt = Date.now() / 1000 - backendElapsed;
    }

    // Reset message cycling when the phase changes so messages start from index 0.
    if (_currentPhase !== phase) {
      _currentPhase = phase;
      _msgTick = 0;
    }

    set({
      elapsed: Math.floor(Date.now() / 1000 - _startAt),
      msgTick: _msgTick,
    });

    if (_intervalId === null) {
      _intervalId = setInterval(() => {
        if (_startAt !== null) {
          _msgTick++;
          set({
            elapsed: Math.floor(Date.now() / 1000 - _startAt),
            msgTick: _msgTick,
          });
        }
      }, 1000);
    }
  },

  stop: () => {
    if (_intervalId !== null) {
      clearInterval(_intervalId);
      _intervalId = null;
    }
    _startAt = null;
    _currentPhase = null;
    _msgTick = 0;
    set({ elapsed: 0, msgTick: 0 });
  },
}));
