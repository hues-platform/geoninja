/**
 * Mapping helpers for `KeyValueTable`.
 *
 * The results UI renders several different sources of data in a uniform
 * key/value table component:
 * - the parameter registry captured in an analysis run context (frontend-defined)
 * - the analysis result items returned by the backend (backend-defined)
 *
 * These helpers normalize those shapes into `KeyValueRow[]`.
 *
 * Scaling and units:
 * - For run-context params, numeric values are scaled using
 *   `param.displayScaleFactor` (base → display) and units use
 *   `param.displayUnit ?? param.unit`.
 * - For result items, scaling is driven by `ANALYSIS_RESULT_META` (contract/UI
 *   metadata), while the backend-provided unit is used as a fallback.
 */

import type { KeyValueRow } from "../common/KeyValueTable";
import { ANALYSIS_RESULT_META } from "../../config/analysisResultMeta";
import type { AnalysisResultItemVM } from "../../types/analysisRun";
import type { ParamRegistry } from "../../types/params";

export function contextParamsToKeyValueRows(
  params: ParamRegistry | null | undefined,
): KeyValueRow[] {
  /**
   * Convert a captured parameter registry into `KeyValueRow[]`.
   *
   * For each param:
   * - strings: emit the effective value (`value` then `default`) or `null`
   * - numbers: emit the effective value scaled into display units, or `null`
   */
  if (!params) return [];

  return Object.entries(params).map(([key, param]) => {
    const base = {
      key,
      name: param.name ?? key,
      description: param.description ?? null,
    };

    if (param.valueType === "string") {
      return {
        ...base,
        valueType: "string" as const,
        value:
          typeof param.value === "string"
            ? param.value
            : typeof param.default === "string"
              ? param.default
              : null,
      };
    }

    // number or null
    const raw =
      typeof param.value === "number"
        ? param.value
        : typeof param.default === "number"
          ? param.default
          : null;

    const scale = param.displayScaleFactor ?? 1;

    return {
      ...base,
      valueType: "number" as const,
      value: raw == null ? null : raw * scale,
      unit: param.displayUnit ?? param.unit,
    };
  });
}

export function analysisResultItemsToKeyValueRows(
  items: AnalysisResultItemVM[] | null | undefined,
): KeyValueRow[] {
  /**
   * Convert backend analysis result items into `KeyValueRow[]`.
   *
   * Uses `ANALYSIS_RESULT_META` for user-facing labels/description and optional
   * display scaling. In dev, missing metadata emits a console warning.
   */
  if (!items) return [];

  return items.map((it) => {
    const meta = ANALYSIS_RESULT_META[it.key];
    if (!meta && import.meta.env.DEV) {
      console.warn(`[AnalysisResultMeta] Missing meta entry for result key "${it.key}"`);
    }

    const base = {
      key: it.key,
      name: meta?.name ?? it.key,
      description: meta?.description ?? null,
    };

    if (typeof it.value === "string") {
      return { ...base, valueType: "string" as const, value: it.value };
    }

    // number or null
    const raw = typeof it.value === "number" ? it.value : null;
    const scale = meta?.displayScaleFactor ?? 1;
    const scaled = raw == null ? null : raw * scale;

    return {
      ...base,
      valueType: "number" as const,
      value: scaled,
      unit: meta?.displayUnit ?? it.unit ?? "",
    };
  });
}
