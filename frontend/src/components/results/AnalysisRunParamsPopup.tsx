/**
 * Run-parameter viewer.
 *
 * Renders a button that toggles a lightweight overlay dialog showing the
 * parameters used for a particular analysis run (provided as preformatted
 * `KeyValueRow[]`).
 *
 * Close interactions:
 * - Escape closes the popup when open.
 * - Clicking outside the dialog (on the overlay) closes it.
 */
import { useState, type CSSProperties } from "react";
import KeyValueTable, { type KeyValueRow } from "../common/KeyValueTable";
import { useEscapeKey } from "../../hooks/useEscapeKey";

type AnalysisRunPopupProps = {
  /** Table rows to render (typically derived from an analysis run context). */
  rows: KeyValueRow[];

  /** Disables the toggle button (e.g. when no run context exists). */
  disabled?: boolean;

  /** Optional button label override. */
  buttonLabel?: string;

  /** Optional button tooltip/title override. */
  buttonTitle?: string;
};

export function AnalysisRunParamsPopup({
  rows,
  disabled = false,
  buttonLabel = "Run parameters",
  buttonTitle = "Show Run parameters",
}: AnalysisRunPopupProps) {
  const [open, setOpen] = useState(false);

  useEscapeKey(open, () => setOpen(false));

  return (
    <>
      <button
        style={styles.paramsBtn}
        onClick={() => setOpen((v) => !v)}
        disabled={disabled}
        title={disabled ? "No run context available" : buttonTitle}
      >
        {buttonLabel}
      </button>

      {open && (
        <div style={styles.popupOverlay} onClick={() => setOpen(false)}>
          <div style={styles.popup} onClick={(e) => e.stopPropagation()}>
            <div style={styles.popupHeader}>
              <div style={{ fontWeight: 700 }}>Run parameters</div>
              <button
                type="button"
                style={styles.popupCloseBtn}
                onClick={() => setOpen(false)}
                aria-label="Close parameters"
              >
                ✕
              </button>
            </div>

            <div style={styles.popupBody}>
              <KeyValueTable rows={rows} maxHeight="55vh" />
            </div>
          </div>
        </div>
      )}
    </>
  );
}

const styles: Record<string, CSSProperties> = {
  paramsBtn: {
    border: "1px solid rgba(0,0,0,0.2)",
    background: "white",
    borderRadius: 8,
    cursor: "pointer",
    padding: "4px 10px",
    fontSize: 12,
    fontWeight: 600,
  },

  popupOverlay: {
    position: "absolute",
    inset: 0,
    background: "rgba(0,0,0,0.10)",
    display: "flex",
    alignItems: "flex-start",
    justifyContent: "center",
    padding: 16,
    zIndex: 9999,
  },

  popup: {
    width: "min(760px, 100%)",
    maxHeight: "calc(100% - 32px)",
    background: "white",
    border: "1px solid rgba(0,0,0,0.12)",
    borderRadius: 10,
    boxShadow: "0 10px 30px rgba(0,0,0,0.2)",
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
  },

  popupHeader: {
    padding: "10px 12px",
    borderBottom: "1px solid rgba(0,0,0,0.1)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },

  popupCloseBtn: {
    border: "1px solid rgba(0,0,0,0.2)",
    background: "white",
    borderRadius: 8,
    cursor: "pointer",
    padding: "2px 8px",
  },

  popupBody: {
    padding: 12,
    overflow: "auto",
  },
};
