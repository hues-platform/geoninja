/**
 * DTO → VM adapter for analysis run results.
 *
 * The backend response types come from the generated OpenAPI schema and use
 * snake_case fields with optional/null-ish values.
 *
 * This module converts those DTOs into UI-friendly view models:
 * - snake_case → camelCase
 * - missing/undefined optional fields → explicit `null` where the UI expects it
 * - lists default to empty arrays
 */

import type { components } from "../api/_generated/openapi.types";
import type { AnalysisRunResultsVM, AnalysisResultItemVM } from "../types/analysisRun";

type AnalysisRunResultsDTO = components["schemas"]["AnalysisRunResults"];
type AnalysisResultItemDTO = components["schemas"]["AnalysisResultItem"];

/**
 * Adapt a single analysis result item.
 *
 * The VM uses `null` (not `undefined`) for missing value/unit so components can
 * render consistently without extra checks.
 */
function adaptItem(it: AnalysisResultItemDTO): AnalysisResultItemVM {
  return {
    key: it.key,
    value: it.value ?? null,
    unit: it.unit ?? null,
  };
}

/**
 * Adapt the backend analysis-run results payload into the UI view model.
 *
 * Returns `null` when `dto` is null/undefined so callers can treat
 * “no payload” distinctly from “payload with empty results”.
 */
export function adaptAnalysisRunResults(
  dto: AnalysisRunResultsDTO | null | undefined,
): AnalysisRunResultsVM | null {
  if (!dto) return null;

  return {
    atesKpiResults: (dto.ates_kpi_results ?? []).map(adaptItem),
    derivedQuantities: (dto.derived_quantities ?? []).map(adaptItem),
    status: dto.status,
    message: dto.message ?? null,
  };
}
