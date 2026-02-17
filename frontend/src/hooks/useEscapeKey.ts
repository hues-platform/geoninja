/**
 * Escape-key handling hook with a global “topmost wins” policy.
 *
 * Multiple overlays/popups can be open at once (e.g. results panel + nested
 * parameter dialog). This hook ensures that only the most recently enabled
 * consumer handles the Escape key.
 *
 * Implementation notes:
 * - Each hook instance registers a unique id via `useId()`.
 * - Enabled instances push their id onto a shared module-level stack.
 * - Only the stack top receives Escape events.
 * - Cleanup removes the id even if unmount order differs.
 */

import { useEffect, useId } from "react";

// Module-level stack shared across all hook users
const escapeStack: string[] = [];

function isTop(id: string) {
  return escapeStack.length > 0 && escapeStack[escapeStack.length - 1] === id;
}

export function useEscapeKey(enabled: boolean, onEscape: () => void) {
  /**
   * Register an Escape key listener while `enabled`.
   *
   * Args:
   * - `enabled`: when false, no listener is attached and the instance is not on the stack
   * - `onEscape`: callback invoked when Escape is pressed and this instance is topmost
   */
  const id = useId();

  useEffect(() => {
    if (!enabled) return;

    // Push on mount/enable
    escapeStack.push(id);

    const handler = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (!isTop(id)) return;
      e.preventDefault();
      e.stopPropagation();
      onEscape();
    };

    window.addEventListener("keydown", handler);
    return () => {
      window.removeEventListener("keydown", handler);

      // Remove this id from stack (handle out-of-order unmounts)
      const idx = escapeStack.lastIndexOf(id);
      if (idx >= 0) escapeStack.splice(idx, 1);
    };
  }, [enabled, id, onEscape]);
}
