/**
 * Analysis run API client.
 *
 * This module wraps the backend `POST /api/analysis/run` endpoint.
 * Request/response types are derived from the generated OpenAPI TypeScript
 * definitions to keep the frontend aligned with the committed contract.
 *
 * Error handling:
 * - Non-2xx responses throw an `ApiError` with a short user-facing message.
 * - Network errors throw a plain `Error`.
 * - Aborted requests rethrow the `AbortError` so callers can ignore it.
 */

import type { ParamRegistry, LatLng } from "../types/params";
import { ApiError, buildHttpErrorMessage, safeReadText } from "./apiError";
import type { paths } from "./_generated/openapi.types";
type AnalysisRunPath = paths["/api/analysis/run"];

export type AnalysisRunRequest =
  AnalysisRunPath["post"]["requestBody"]["content"]["application/json"];

export type AnalysisRunResponse =
  AnalysisRunPath["post"]["responses"]["200"]["content"]["application/json"];

export type AnalysisRunStatus = "ok" | "error";

function buildEffectiveParams(params: ParamRegistry): AnalysisRunRequest["params"] {
  /**
   * Convert the UI param registry into the backend request payload.
   *
   * The backend expects the “effective” scalar value for each key: `value` if
   * set, otherwise `default`. Missing/undefined values are omitted.
   */
  const out = {} as AnalysisRunRequest["params"];

  for (const [key, p] of Object.entries(params)) {
    if (p.valueType === "number") {
      const val = p.value ?? p.default;
      if (typeof val === "number") out[key] = val;
      continue;
    }

    const val = p.value ?? p.default;
    if (typeof val === "string") out[key] = val;
  }

  return out;
}

export async function runAnalysis(args: {
  pos: LatLng;
  params: ParamRegistry;
  runId?: AnalysisRunRequest["runId"];
  startedAt?: AnalysisRunRequest["startedAt"];
  optInputs?: AnalysisRunRequest["optInputs"];
  signal?: AbortSignal;
}): Promise<AnalysisRunResponse> {
  /**
   * Trigger a backend analysis run at a given location.
   *
   * Args:
   * - `pos`: WGS84 (lat/lng)
   * - `params`: UI registry; values are reduced to a backend `params` object
   * - `signal`: optional abort signal
   */
  const { pos, params, runId, startedAt, optInputs, signal } = args;

  const req: AnalysisRunRequest = {
    location: { lat: pos.lat, lng: pos.lng },
    params: buildEffectiveParams(params),
    runId,
    startedAt,
    optInputs: optInputs,
  };

  const url = "/api/analysis/run";

  let resp: Response;
  try {
    resp = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(req),
      signal,
    });
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") throw e;
    throw new Error(`Network error while calling ${url}`);
  }

  if (!resp.ok) {
    const text = await safeReadText(resp);
    const msg = buildHttpErrorMessage(resp.status, text);
    console.error("runAnalysis: HTTP error", resp.status, text);
    throw new ApiError({
      message: msg,
      status: resp.status,
      url,
      bodyText: text,
    });
  }

  return (await resp.json()) as AnalysisRunResponse;
}
