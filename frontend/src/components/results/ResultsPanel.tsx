/**
 * Results overlay panel.
 *
 * Displays analysis output for the most recent run:
 * - A title derived from the run location (if context exists)
 * - A button to open a popup with the parameters used in the run, plus derived
 *   quantities returned by the backend
 * - A compact table of ATES KPI results
 *
 * Close interactions:
 * - Escape closes the panel when `open`.
 * - Clicking the backdrop closes; clicking inside the panel does not.
 */
import { type CSSProperties } from "react";
import type { AnalysisRunContext } from "../../types/analysisRun";
import type { KeyValueRow } from "../common/KeyValueTable";
import KeyValueTable from "../common/KeyValueTable";
import { AnalysisRunParamsPopup } from "./AnalysisRunParamsPopup";
import type { AnalysisRunResultsVM } from "../../types/analysisRun";
import {
  contextParamsToKeyValueRows,
  analysisResultItemsToKeyValueRows,
} from "../common/keyValueRowMapper";
import { useEscapeKey } from "../../hooks/useEscapeKey";

type ResultsPanelProps = {
  /** Whether the panel is mounted and interactive. */
  open: boolean;

  /** Run context, including location and the (frozen) parameter registry used. */
  context: AnalysisRunContext | null;

  /** View-model of backend analysis results; may be null/undefined before any run. */
  results?: AnalysisRunResultsVM | null;

  /** Close callback used by Escape key, backdrop click, and close button. */
  onClose: () => void;
};

export function ResultsPanel({ open, context, results, onClose }: ResultsPanelProps) {
  useEscapeKey(open, onClose);
  if (!open) return null;

  const title = context
    ? `Results at (${context.location.lat.toFixed(4)}, ${context.location.lng.toFixed(4)})`
    : "Results";

  // Rows from the run context (i.e. front-end defined parameters) for the pop-up
  const contextRowsForPopup = contextParamsToKeyValueRows(context?.params);
  // Derived rows from the back-end for the pop-up
  const derivedRowsForPopup: KeyValueRow[] = analysisResultItemsToKeyValueRows(
    results?.derivedQuantities,
  );
  // Combine both
  const rowsForPopup: KeyValueRow[] = [...contextRowsForPopup, ...derivedRowsForPopup];
  // ATES KPI rows for table rendering
  const atesKpiRows: KeyValueRow[] = analysisResultItemsToKeyValueRows(results?.atesKpiResults);

  const hasResults = !!results && results.status == "ok";
  const hasAtesKpis = (atesKpiRows?.length ?? 0) > 0;

  return (
    <div style={styles.backdrop} onClick={onClose}>
      <div style={styles.panel} onClick={(e) => e.stopPropagation()}>
        <div style={styles.header}>
          <div style={styles.title}>{title}</div>
          <button style={styles.closeBtn} onClick={onClose} aria-label="Close results">
            ✕
          </button>
        </div>
        <div style={styles.body}>
          {/* Analysis run parameters popup */}
          <div style={styles.actionsRow}>
            <span style={styles.actionsLabel}>Parameters used in this run:</span>
            <AnalysisRunParamsPopup rows={rowsForPopup} disabled={!context} buttonLabel="Open" />
          </div>

          {/* ATES KPI results table */}
          <div style={styles.section}>
            <div style={styles.sectionHeader}>ATES KPIs</div>
            {!hasResults ? (
              <div style={styles.muted}>Run the analysis to see KPI results.</div>
            ) : !hasAtesKpis ? (
              <div style={styles.muted}>No ATES KPI results available.</div>
            ) : (
              <KeyValueTable rows={atesKpiRows} maxHeight="45vh" />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  backdrop: {
    position: "fixed",
    inset: 0,
    background: "rgba(0,0,0,0.35)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 2000,
    padding: 16,
  },
  panel: {
    height: "clamp(320px, 75vh, 650px)",
    width: "clamp(360px, 70vw, 600px)",
    background: "#fff",
    borderRadius: 12,
    boxShadow: "0 20px 60px rgba(0,0,0,0.35)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    position: "relative",
  },
  header: {
    position: "relative",
    padding: "12px 12px",
    borderBottom: "1px solid rgba(0,0,0,0.1)",
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
  },
  title: { fontWeight: 700 },
  body: {
    padding: 12,
    overflow: "auto",
    flex: 1,
    position: "relative",
  },

  actionsRow: {
    display: "inline-flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 12,
    fontSize: 12,
  },

  actionsLabel: {
    fontWeight: 600,
    opacity: 0.85,
  },
  closeBtn: {
    position: "absolute",
    top: 8,
    right: 8,
    border: "1px solid rgba(0,0,0,0.2)",
    background: "white",
    borderRadius: 8,
    cursor: "pointer",
    padding: "4px 8px",
  },
  section: {
    marginTop: 12,
    paddingTop: 10,
    borderTop: "1px solid rgba(0,0,0,0.08)",
  },
  sectionHeader: {
    fontWeight: 700,
    fontSize: 12,
    marginBottom: 8,
    opacity: 0.9,
  },
  muted: {
    fontSize: 12,
    opacity: 0.7,
  },
  statusError: {
    border: "1px solid rgba(255,0,0,0.25)",
    background: "rgba(255,0,0,0.06)",
    padding: "8px 10px",
    borderRadius: 8,
    fontSize: 12,
    marginBottom: 10,
  },
};
