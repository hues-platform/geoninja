/**
 * Error toast store.
 *
 * This is a small, UI-facing Zustand store used for transient error messages.
 *
 * Design notes:
 * - `pushError()` returns an id so callers can dismiss programmatically.
 * - Each toast is auto-dismissed after `durationMs` via a timeout.
 * - Auto-dismiss checks the toast still exists before removing it.
 */

import { create } from "zustand";

export type ErrorToast = {
  id: string;
  message: string;
  createdAt: number;
  durationMs: number;
};

type PushErrorOptions = {
  durationMs?: number;
};

type ErrorState = {
  errors: ErrorToast[];
  pushError: (message: string, options?: PushErrorOptions) => string;
  dismissError: (id: string) => void;
  clearErrors: () => void;
};

const DEFAULT_DURATION_MS = 5000;

// Create a reasonably-unique id for a toast.
function newId(): string {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export const useErrorStore = create<ErrorState>((set, get) => ({
  errors: [],

  pushError: (message, options) => {
    const id = newId();
    const durationMs = options?.durationMs ?? DEFAULT_DURATION_MS;

    const toast: ErrorToast = {
      id,
      message,
      createdAt: Date.now(),
      durationMs,
    };

    set((s) => ({ errors: [...s.errors, toast] }));

    window.setTimeout(() => {
      if (get().errors.some((e) => e.id === id)) {
        get().dismissError(id);
      }
    }, durationMs);

    return id;
  },

  dismissError: (id) => set((s) => ({ errors: s.errors.filter((e) => e.id != id) })),

  clearErrors: () => set({ errors: [] }),
}));
