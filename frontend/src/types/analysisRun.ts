/**
 * Analysis run domain types.
 *
 * These types sit between:
 * - backend DTOs (from generated OpenAPI types), and
 * - UI view models and workflow context stored in the app store.
 *
 * Naming:
 * - `DTO` types mirror the backend API schema.
 * - `VM` types are view models used by components.
 */

import type { components } from "../api/_generated/openapi.types";
import type { LatLng } from "./params";
import type { ParamRegistry } from "./params";

type AnalysisRunResultsDTO = components["schemas"]["AnalysisRunResults"];

/**
 * Immutable context captured when a user triggers an analysis run.
 *
 * This is intentionally “request-shaped” and stores the inputs needed to
 * reproduce the run request (location + current params) alongside an id/timestamp
 * for UI bookkeeping.
 */
export type AnalysisRunContext = {
  id: number;
  startedAt: number;
  location: LatLng;
  params: ParamRegistry;
};

/**
 * A single result entry ready for UI rendering.
 *
 * `value` and `unit` are nullable because the backend may omit them for certain
 * result keys.
 */
export type AnalysisResultItemVM = {
  key: string;
  value: number | string | null;
  unit: string | null;
};

/**
 * View model for a completed analysis run.
 *
 * `status` is sourced directly from the OpenAPI schema to remain aligned with
 * the backend contract.
 */
export type AnalysisRunResultsVM = {
  atesKpiResults: AnalysisResultItemVM[];
  derivedQuantities: AnalysisResultItemVM[];
  status: AnalysisRunResultsDTO["status"];
  message: string | null;
};
