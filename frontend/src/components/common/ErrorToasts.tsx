/**
 * Global error toasts.
 *
 * Renders a stack of dismissible error messages sourced from `useErrorStore`.
 * This is used for cross-cutting failures (API errors, unexpected exceptions)
 * that should be visible regardless of which panel is currently open.
 *
 * Behavior:
 * - When there are no errors, renders `null`.
 * - Each toast can be dismissed via the close button (calls `dismissError`).
 * - Uses `aria-live="polite"` so screen readers announce new messages.
 */
import { useErrorStore } from "../../process/errorStore";

export default function ErrorToasts() {
  const errors = useErrorStore((s) => s.errors);
  const dismiss = useErrorStore((s) => s.dismissError);

  if (errors.length === 0) return null;

  return (
    <div style={styles.container} aria-live="polite" aria-relevant="additions">
      {errors.map((e) => (
        <div key={e.id} style={styles.toast} role="status">
          <div style={{ flex: 1 }}>
            <div style={styles.titleRow}>
              <span style={styles.badge}>Error</span>
              <span style={{ fontSize: 12, opacity: 0.7 }}>
                {new Date(e.createdAt).toLocaleTimeString()}
              </span>
            </div>
            <p style={styles.message}>{e.message}</p>
          </div>

          <button
            type="button"
            style={styles.closeBtn}
            onClick={() => dismiss(e.id)}
            aria-label="Dismiss error"
            title="Dismiss"
          >
            ×
          </button>
        </div>
      ))}
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    position: "absolute",
    top: 14,
    left: "50%",
    transform: "translateX(-50%)",
    zIndex: 9999,
    display: "flex",
    flexDirection: "column",
    gap: 10,
    width: "min(720px, calc(100% - 24px))",
    pointerEvents: "none", // clicks pass through except on the toast
  },
  toast: {
    pointerEvents: "auto",
    background: "rgba(20, 20, 20, 0.92)",
    color: "white",
    borderRadius: 12,
    padding: "10px 12px",
    boxShadow: "0 6px 20px rgba(0,0,0,0.25)",
    border: "1px solid rgba(255,255,255,0.10)",
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "space-between",
    gap: 12,
  },
  message: {
    fontSize: 14,
    lineHeight: 1.35,
    margin: 0,
    whiteSpace: "pre-wrap",
    overflowWrap: "anywhere",
  },
  closeBtn: {
    background: "transparent",
    border: "none",
    color: "rgba(255,255,255,0.75)",
    cursor: "pointer",
    fontSize: 18,
    lineHeight: 1,
    padding: "2px 6px",
    borderRadius: 8,
  },
  titleRow: {
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 4,
  },
  badge: {
    display: "inline-block",
    fontSize: 12,
    padding: "2px 8px",
    borderRadius: 999,
    background: "rgba(255, 80, 80, 0.18)",
    border: "1px solid rgba(255, 80, 80, 0.35)",
    color: "rgba(255,255,255,0.9)",
  },
};
