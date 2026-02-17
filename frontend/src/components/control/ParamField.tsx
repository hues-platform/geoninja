/**
 * Single parameter input field.
 *
 * Renders either a numeric or string input based on `param.valueType`.
 *
 * Numeric UX details:
 * - Uses a local “raw” string buffer while focused so partial inputs like `0.`
 *   are preserved during editing.
 * - Commits to the parent only when the input parses to a finite number.
 * - Converts between base units and display units via `displayScaleFactor`.
 *
 * Validation:
 * - Prefers caller-provided `validity` (typically computed centrally).
 * - Falls back to minimal inline validation when `validity` is omitted.
 */
import { useState, type CSSProperties } from "react";
import type { NumericParam, Param } from "../../types/params";
import { getEffectiveValue, isChangedFromDefault } from "../../types/params";
import type { ParamValidity } from "../../config/paramValidation";
import InfoToolTip from "../common/InfoToolTip";

const SMALL_NUMBER_THRESHOLD = 0.001;
const SMALL_NUMBER_DECIMALS = 3;
const DISPLAY_SIG_DIGITS = 6;

export type ParamFieldProps = {
  /** Parameter definition + current value/defaults. */
  param: Param;

  /** Bubble-up handler called with the param key and the new scalar value. */
  onChange: (key: string, value: number | string) => void;

  /** Whether to show the reset-to-default indicator when the value differs. */
  showChangedIndicator?: boolean;

  /** Optional validation result (preferred over internal fallback validation). */
  validity?: ParamValidity;
};

export function ParamField({
  param: p,
  onChange,
  showChangedIndicator = true,
  validity: validityProp,
}: ParamFieldProps) {
  const eff = getEffectiveValue(p);
  const changed = isChangedFromDefault(p);

  // Local buffer ONLY while editing numeric inputs (prevents 0. -> 0 collapse)
  const [isEditingNumber, setIsEditingNumber] = useState(false);
  const [rawNumber, setRawNumber] = useState("");

  const displayNumber =
    p.valueType === "number"
      ? isEditingNumber
        ? rawNumber
        : typeof eff === "number"
          ? formatNumberForDisplay(toDisplayNumber(p, eff))
          : ""
      : "";

  const validity: ParamValidity = (() => {
    // If caller provides a validity result, trust it
    if (validityProp) return validityProp;

    // Fallback (keeps ParamField usable if called without validity)
    if (eff === undefined) return { isValid: false, reason: "Missing value" };

    if (p.valueType === "number") {
      if (typeof eff !== "number") return { isValid: false, reason: "Not a number" };
      if (p.min !== undefined && eff < p.min)
        return { isValid: false, reason: `Value below minimum of ${p.min}` };
      if (p.max !== undefined && eff > p.max)
        return { isValid: false, reason: `Value above maximum of ${p.max}` };
      return { isValid: true };
    }

    // string
    if (typeof eff !== "string") return { isValid: false, reason: "Not a string" };
    if (eff.trim().length === 0) return { isValid: false, reason: "Empty string" };
    return { isValid: true };
  })();

  const isInvalid = !validity.isValid;

  const resetToDefault = () => {
    if (!p.editable) return;
    if (p.default === undefined) return;
    // If user is mid-edit on numeric field, clear buffer so reset is visible directly
    setIsEditingNumber(false);
    setRawNumber("");

    // Reset current value to default
    onChange(p.key, p.default);
  };

  return (
    <div style={styles.container}>
      {/* Header */}
      <div style={styles.headerRow}>
        <div style={styles.label}>
          <span title={p.description ?? ""}>
            {p.name}
            {p.valueType === "number" && getDisplayUnit(p) ? (
              <span style={styles.unit}> [{getDisplayUnit(p)}]</span>
            ) : null}
          </span>

          {p.description ? (
            <span style={styles.tooltipInline}>
              <InfoToolTip
                tooltip={
                  p.valueType === "number" && p.min !== undefined && p.max !== undefined
                    ? (() => {
                        const unit = getDisplayUnit(p);
                        const unitSuffix = unit && unit !== "-" ? unit : "";
                        const lb = formatNumberForDisplay(toDisplayNumber(p, p.min));
                        const ub = formatNumberForDisplay(toDisplayNumber(p, p.max));
                        return (
                          <>
                            <div>{p.description}.</div>
                            <div>
                              Must be between {lb} {unitSuffix} and {ub} {unitSuffix}.
                            </div>
                          </>
                        );
                      })()
                    : p.description
                }
                iconChar="?"
                iconBgColor="#1e6bd6"
                iconColor="white"
                placement="right"
              />
            </span>
          ) : null}
        </div>
      </div>

      {/* Input row */}
      <div style={styles.inputRow}>
        {p.valueType === "number" ? (
          <input
            className="noNumberSpinner"
            type="text"
            inputMode="decimal"
            lang="en-US"
            value={displayNumber}
            disabled={!p.editable}
            onFocus={() => {
              setIsEditingNumber(true);
              setRawNumber(
                typeof eff === "number" ? formatNumberForDisplay(toDisplayNumber(p, eff)) : "",
              );
            }}
            onBlur={() => {
              // If the user cleared the field (or left it in a partial state) and leaves the input,
              // commit a deterministic value instead of restoring the previous number.
              if (p.editable) {
                const trimmed = rawNumber.trim();
                if (trimmed === "" || trimmed === "." || trimmed === "-" || trimmed === "-.") {
                  onChange(p.key, 0);
                }
              }
              setIsEditingNumber(false);
              setRawNumber("");
            }}
            onChange={(e) => {
              // Normalize comma to dot (optional convenience)
              const next = e.target.value.replace(",", ".");
              setRawNumber(next);

              // Allow empty / partial states while typing
              if (next.trim() === "" || next === "." || next === "-" || next === "-.") {
                return;
              }

              // Only commit when parseable
              const n = Number(next);
              if (!Number.isFinite(n)) return;

              onChange(p.key, toBaseNumber(p, n));
            }}
            style={{
              ...styles.input,
              ...(isInvalid ? styles.inputInvalid : undefined),
              ...(!p.editable ? styles.inputDisabled : undefined),
            }}
          />
        ) : (
          <input
            type="text"
            value={typeof eff === "string" ? eff : (eff ?? "")}
            disabled={!p.editable}
            onChange={(e) => onChange(p.key, e.target.value)}
            onBlur={(e) => {
              if (!p.editable) return;
              // Normalize whitespace-only strings to empty on blur.
              if (e.target.value.trim().length === 0) {
                onChange(p.key, "");
              }
            }}
            style={{
              ...styles.input,
              ...(isInvalid ? styles.inputInvalid : undefined),
              ...(!p.editable ? styles.inputDisabled : undefined),
            }}
          />
        )}

        {/* Right-side indicator column */}
        <div style={styles.indicatorBox}>
          {/* Reset button (shown only if value differs from default) */}
          {showChangedIndicator && changed && p.editable ? (
            <button
              type="button"
              onClick={resetToDefault}
              style={styles.resetBtn}
              title="Reset to default"
              aria-label={`Reset ${p.name} to default`}
            >
              ↺
            </button>
          ) : null}

          {/* Invalid indicator */}
          {isInvalid ? (
            <InfoToolTip
              tooltip={validity.reason ?? "Invalid value."}
              iconChar="!"
              size={14}
              iconBgColor="#c62828"
              iconColor="white"
              placement="left"
            />
          ) : null}
        </div>
      </div>
    </div>
  );
}

function formatSmallScientific(value: number): string {
  if (!Number.isFinite(value)) return "";
  if (value === 0) return "0";

  const abs = Math.abs(value);
  let exp = Math.floor(Math.log10(abs));
  let mantissa = abs / Math.pow(10, exp);
  const sign = value < 0 ? "-" : "";

  // Round mantissa; if rounding pushes it to 10, renormalize
  const rounded = Number(mantissa.toFixed(SMALL_NUMBER_DECIMALS));
  if (rounded >= 10) {
    mantissa = rounded / 10;
    exp += 1;
  } else {
    mantissa = rounded;
  }

  // Trim trailing zeros for cleaner display (e.g. 5.000 -> 5)
  const mantissaStr = mantissa
    .toFixed(SMALL_NUMBER_DECIMALS)
    .replace(/\.0+$|(?<=\.[0-9]*?)0+$/, "")
    .replace(/\.$/, "");

  return `${sign}${mantissaStr}e${exp}`;
}

function formatNumberForDisplay(value: number): string {
  if (!Number.isFinite(value)) return "";
  if (value === 0) return "0";

  const abs = Math.abs(value);

  // Keep your existing scientific formatting for tiny values
  if (abs > 0 && abs < SMALL_NUMBER_THRESHOLD) return formatSmallScientific(value);

  // Use significant digits for general readability
  // Example: 0.0044416207 -> "0.00444162"
  const s = value.toPrecision(DISPLAY_SIG_DIGITS);

  // toPrecision may produce scientific notation for large/small numbers.
  // If you don't want that except for < SMALL_NUMBER_THRESHOLD, normalize:
  // (optional: only needed if you see "1.23e+5" in the UI)
  if (s.includes("e")) {
    // fallback: fixed decimals based on magnitude
    const decimals = abs < 1 ? 6 : abs < 100 ? 3 : 1;
    return value
      .toFixed(decimals)
      .replace(/\.0+$|(?<=\.[0-9]*?)0+$/, "")
      .replace(/\.$/, "");
  }

  // Trim trailing zeros and trailing dot
  return s.replace(/\.0+$|(?<=\.[0-9]*?)0+$/, "").replace(/\.$/, "");
}

function getDisplayUnit(p: Param): string | undefined {
  return p.valueType === "number" ? (p.displayUnit ?? p.unit) : undefined;
}

function toDisplayNumber(p: NumericParam, baseValue: number): number {
  const s = p.displayScaleFactor ?? 1;
  return baseValue * s;
}

function toBaseNumber(p: NumericParam, displayValue: number): number {
  const s = p.displayScaleFactor ?? 1;
  return displayValue / s;
}

const styles: Record<string, CSSProperties> = {
  container: {
    marginBottom: 12,
  },
  headerRow: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 4,
  },
  label: {
    fontSize: 11,
    fontWeight: 600,
    lineHeight: 1.2,
    paddingRight: 10,
  },
  unit: {
    fontWeight: 400,
    color: "rgba(0,0,0,0.65)",
    marginLeft: 2,
  },
  inputRow: {
    display: "flex",
    alignItems: "center", // vertically align indicators with the input
    gap: 10,
  },
  input: {
    flex: 1,
    height: 20,
    padding: "0 10px",
    borderRadius: 6,
    border: "1px solid rgba(0,0,0,0.25)",
    outline: "none",
    fontSize: 10,
    boxSizing: "border-box", // prevents width jitter between valid/invalid styles
  },
  inputDisabled: {
    background: "rgba(0,0,0,0.04)",
    cursor: "not-allowed",
    opacity: 0.85,
  },
  inputInvalid: {
    border: "1px solid #c62828",
    background: "rgba(198, 40, 40, 0.04)",
  },
  indicatorBox: {
    display: "flex",
    alignItems: "center",
    gap: 4,
    marginLeft: 4,
  },
  indicatorPlaceholder: {
    display: "inline-block",
    width: 1,
    height: 1,
  },
  tooltipInline: {
    display: "inline-flex",
    alignItems: "center",
    marginLeft: 8,
  },
  resetBtn: {
    width: 18,
    height: 18,
    padding: 0,
    border: "none",
    background: "transparent",
    cursor: "pointer",
    fontSize: 14,
    lineHeight: "18px",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    color: "rgba(0,0,0,0.6)",
  },
  containerHighlighted: {
    padding: 6,
    borderRadius: 8,
    outline: "2px solid rgba(198, 40, 40, 0.25)",
    outlineOffset: 2,
    background: "rgba(198, 40, 40, 0.03)",
  },
};
