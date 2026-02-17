/**
 * Generic key/value table.
 *
 * Used throughout the UI to render both:
 * - analysis run context parameters (frontend-defined)
 * - backend analysis result items (backend-defined)
 *
 * Rows are passed in as `KeyValueRow[]` (already mapped into display units).
 * This component is responsible only for presentation:
 * - consistent numeric formatting
 * - optional description tooltips
 * - optional scroll container via `maxHeight`
 */

import type { CSSProperties } from "react";
import InfoTooltip from "./InfoToolTip";

export type KeyValueRow =
  | {
      /** Stable identifier used as React row key (often a contract key). */
      key: string;

      /** Human-readable row label. */
      name: string;

      /** Optional description displayed in an info tooltip. */
      description?: string | null;

      /** Numeric row. */
      valueType: "number";

      /** Numeric value (already in display units) or `null` when missing. */
      value: number | null;

      /** Optional unit string for display. */
      unit?: string;
    }
  | {
      /** Stable identifier used as React row key (often a contract key). */
      key: string;

      /** Human-readable row label. */
      name: string;

      /** Optional description displayed in an info tooltip. */
      description?: string | null;

      /** String row. */
      valueType: "string";

      /** String value or `null` when missing. */
      value: string | null;

      /** String rows do not display units (kept for union symmetry). */
      unit?: "";
    };

type KeyValueTableProps = {
  /** Rows to render (already mapped/ordered by the caller). */
  rows: KeyValueRow[];

  /** Optional max height for a scrollable wrapper (e.g. `"55vh"`). */
  maxHeight?: number | string;
};

function formatValue(row: KeyValueRow): string {
  if (row.value == null) return "–";

  if (row.valueType === "string") {
    return row.value;
  }

  return formatNumber(row.value);
}

function formatNumber(v: number): string {
  if (!Number.isFinite(v)) return String(v);
  if (v === 0) return "0";

  const abs = Math.abs(v);

  // Very small or very large → scientific notation (compact + readable)
  if (abs < 1e-3 || abs >= 1e7) {
    // 3 significant digits (roughly)
    return v.toExponential(2);
  }

  // Large-ish → grouping separators, minimal decimals
  if (abs >= 1e4) {
    return new Intl.NumberFormat("en-US", {
      maximumFractionDigits: 2,
    }).format(v);
  }

  // Normal range → up to 3 decimals, no trailing noise
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: 0,
    maximumFractionDigits: abs < 1 ? 4 : 3,
  }).format(v);
}

function normalizeUnit(unit?: string | null): string {
  return unit ? unit : "";
}

export default function KeyValueTable({ rows, maxHeight }: KeyValueTableProps) {
  return (
    <div style={{ ...styles.wrapper, ...(maxHeight ? { maxHeight } : null) }}>
      <table style={styles.table}>
        <thead>
          <tr>
            <th style={styles.thIcon} />
            <th style={styles.th}>Parameter</th>
            <th style={{ ...styles.th, ...styles.thValue }}>Value</th>
            <th style={styles.th}>Unit</th>
          </tr>
        </thead>

        <tbody>
          {rows.map((r) => {
            const unit = normalizeUnit(r.unit);
            return (
              <tr key={r.key}>
                <td style={styles.tdIcon}>
                  {r.description ? (
                    <InfoTooltip
                      tooltip={r.description}
                      size={12}
                      contentFontSize={10}
                      placement="top"
                      iconChar="i"
                      iconBgColor="#1e6bd6"
                      iconColor="#ffffff"
                    />
                  ) : null}
                </td>

                <td style={styles.tdParam}>{r.name}</td>

                <td style={r.valueType === "number" ? styles.tdMono : styles.td}>
                  {formatValue(r)}
                </td>

                <td style={styles.tdDim}>{unit}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  wrapper: {
    overflow: "auto",
    width: "100%",
  },

  table: {
    width: "100%",
    borderCollapse: "collapse",
    fontSize: 12,
  },

  th: {
    textAlign: "left",
    fontWeight: 700,
    padding: "8px 10px",
    borderBottom: "1px solid rgba(0,0,0,0.12)",
    position: "sticky",
    top: 0,
    background: "white",
    zIndex: 1,
  },

  thValue: {
    width: "30%",
  },

  td: {
    padding: "8px 10px",
    borderBottom: "1px solid rgba(0,0,0,0.06)",
    verticalAlign: "top",
  },

  tdMono: {
    padding: "8px 10px",
    borderBottom: "1px solid rgba(0,0,0,0.06)",
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace",
    verticalAlign: "top",
    whiteSpace: "nowrap",
  },

  tdDim: {
    padding: "8px 10px",
    borderBottom: "1px solid rgba(0,0,0,0.06)",
    opacity: 0.75,
    verticalAlign: "top",
    whiteSpace: "nowrap",
  },

  tdParam: {
    padding: "8px 10px",
    borderBottom: "1px solid rgba(0,0,0,0.06)",
    verticalAlign: "top",
  },

  paramName: {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
  },

  tooltipWrap: {
    display: "inline-flex",
    alignItems: "center",
    marginLeft: 2,
  },

  thIcon: {
    textAlign: "left",
    fontWeight: 700,
    padding: "8px 6px",
    borderBottom: "1px solid rgba(0,0,0,0.12)",
    position: "sticky",
    top: 0,
    background: "white",
    zIndex: 1,
    width: 28,
  },

  tdIcon: {
    padding: "8px 6px",
    borderBottom: "1px solid rgba(0,0,0,0.06)",
    verticalAlign: "top",
    width: 28,
  },
};
