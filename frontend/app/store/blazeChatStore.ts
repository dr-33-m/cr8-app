import { create } from "zustand";
import { BlazeChatState, ChatEntry, ChatEntryKind } from "@/lib/types/stores";

/**
 * Transcript of the current B.L.A.Z.E session.
 *
 * B.L.A.Z.E's replies used to exist only as sonner toasts, which auto-dismiss —
 * so a message that arrived while you were looking at the viewport was simply
 * gone. This keeps the turn-by-turn record, plus the tool activity in between,
 * so the chat dialog can show what actually happened.
 *
 * Deliberately NOT persisted (unlike inboxStore): the backend resets its own
 * conversation history when the browser reconnects, so persisting the UI side
 * would leave the panel showing turns the agent no longer remembers.
 */

let entryCounter = 0;
const nextId = () => `${Date.now()}-${entryCounter++}`;

const makeEntry = (
  kind: ChatEntryKind,
  text: string,
  phase?: string
): ChatEntry => ({
  id: nextId(),
  kind,
  text,
  at: Date.now(),
  ...(phase ? { phase } : {}),
});

export const useBlazeChatStore = create<BlazeChatState>()((set) => ({
  entries: [],
  isBusy: false,
  hasUnseen: false,
  lastRequest: null,

  addUser: (text) =>
    set((state) => ({ entries: [...state.entries, makeEntry("user", text)] })),

  addAssistant: (text) =>
    set((state) => ({
      entries: [...state.entries, makeEntry("assistant", text)],
      hasUnseen: true,
      // The turn landed, so there is nothing left to retry.
      lastRequest: null,
    })),

  addError: (text) =>
    set((state) => ({
      entries: [...state.entries, makeEntry("error", text)],
      hasUnseen: true,
    })),

  addActivity: (phase, text) =>
    set((state) => {
      const last = state.entries[state.entries.length - 1];
      // Collapse a repeat of the same step rather than stacking identical lines
      // (a retried tool can emit the same event several times).
      if (last?.kind === "activity" && last.phase === phase && last.text === text) {
        return state;
      }
      return { entries: [...state.entries, makeEntry("activity", text, phase)] };
    }),

  setBusy: (busy) => set({ isBusy: busy }),

  setLastRequest: (request) => set({ lastRequest: request }),

  markSeen: () => set({ hasUnseen: false }),

  clear: () =>
    set({ entries: [], isBusy: false, hasUnseen: false, lastRequest: null }),
}));

export default useBlazeChatStore;
