/**
 * Local parameters dialog.
 *
 * This popup is opened from the control panel to show parameters whose values
 * are derived from the current map location (and may then be adjusted by the
 * user).
 *
 * Validation:
 * - Per-field validity comes from the parent (`validityByKey`).
 * - Cross-field/group validity (season period overlap/wrapping rules) is computed
 *   here using `validateSeasonPeriods()` and shown as a list of issues.
 *
 * Close interactions:
 * - Escape key closes when `isOpen`.
 * - Clicking the backdrop closes; clicking inside the dialog does not.
 */
import type { CSSProperties } from "react";
import { useEscapeKey } from "../../hooks/useEscapeKey";
import type { Param } from "../../types/params";
import { ParamField } from "./ParamField";
import { validateSeasonPeriods } from "./seasonValidation";
import type { ParamValidity } from "../../config/paramValidation";

type LocalParamsPopupProps = {
  /** Whether the dialog is mounted and interactive. */
  isOpen: boolean;

  /** Params rendered as editable fields in the popup */
  localParams: Param[];

  /** Params used for cross-field / group validation */
  validationParams: Param[];

  /** Per-param validation results */
  validityByKey: Record<string, ParamValidity>;

  /** Close callback used by Escape key, backdrop click, and close button. */
  onClose: () => void;

  /** Bubble-up handler used by each `ParamField`. */
  onParamChange: (key: string, value: number | string) => void;
};

export default function LocalParamsPopup({
  isOpen,
  localParams: params,
  validationParams,
  validityByKey,
  onClose,
  onParamChange,
}: LocalParamsPopupProps) {
  useEscapeKey(isOpen, onClose);

  if (!isOpen) return null;

  const issues = validateSeasonPeriods(validationParams);

  const onBackdropMouseDown = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose();
  };

  return (
    <div style={styles.backdrop} onMouseDown={onBackdropMouseDown} role="presentation">
      {/* Top row: Title and close button */}
      <div
        style={styles.dialog}
        role="dialog"
        aria-modal="true"
        aria-label={"Local parameters"}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <div style={styles.header}>
          <div style={styles.title}>Local parameters</div>

          <button
            type="button"
            onClick={onClose}
            style={styles.closeBtn}
            title="Close"
            aria-label="Close local parameters dialog"
          >
            x
          </button>
        </div>

        {/* Group issues */}
        {issues.length > 0 && (
          <div style={styles.issueBox} role="alert">
            {issues.map((i, idx) => (
              <div key={idx} style={i.severity === "error" ? styles.issueError : styles.issueWarn}>
                {i.message}
              </div>
            ))}
          </div>
        )}

        {/* Parameter fields */}
        <div style={styles.body}>
          {params.length === 0 ? (
            <div style={styles.empty}>No local parameters.</div>
          ) : (
            params
              .slice()
              .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
              .map((p) => (
                <ParamField
                  key={p.key}
                  param={p}
                  onChange={onParamChange}
                  showChangedIndicator={true}
                  validity={validityByKey[p.key]}
                />
              ))
          )}
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  backdrop: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.45)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 9999,
    padding: 16,
  },
  dialog: {
    width: 250,
    maxWidth: "90vw",
    maxHeight: "70vh",
    background: "#fff",
    borderRadius: 10,
    boxShadow: "0 8px 24px rgba(0,0,0,0.2)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    padding: "12px 16px",
    borderBottom: "1px solid rgba(0,0,0,0.12)",
  },
  title: {
    fontSize: 16,
    fontWeight: 600,
  },
  closeBtn: {
    width: 34,
    height: 34,
    borderRadius: 8,
    border: "1px solid rgba(0,0,0,0.15)",
    background: "#fff",
    cursor: "pointer",
    fontSize: 22,
    lineHeight: "22px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
  },
  body: {
    padding: 16,
    overflow: "auto",
  },
  empty: {
    padding: 12,
    border: "1px dashed rgba(0,0,0,0.25)",
    borderRadius: 8,
    color: "rgba(0,0,0,0.7)",
  },
  footer: {
    padding: "12px 16px",
    borderTop: "1px solid rgba(0,0,0,0.12)",
    display: "flex",
    justifyContent: "flex-end",
    gap: 8,
  },
  primaryBtn: {
    padding: "8px 12px",
    borderRadius: 10,
    border: "1px solid rgba(0,0,0,0.15)",
    background: "#fff",
    cursor: "pointer",
    fontWeight: 600,
  },
  issueBox: {
    margin: "12px 16px 0px 16px",
    padding: 10,
    borderRadius: 8,
    border: "1px solid rgba(198, 40, 40, 0.35)",
    background: "rgba(198, 40, 40, 0.06)",
  },
  issueError: {
    color: "rgba(180, 0, 0, 0.95)",
    fontSize: 12,
    lineHeight: "16px",
  },
  issueWarn: {
    color: "rgba(120, 80, 0, 0.95)",
    fontSize: 12,
    lineHeight: "16px",
  },
};
