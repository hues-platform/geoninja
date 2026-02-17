/**
 * Local parameter lookup API client.
 *
 * Wraps `POST /api/local_params/lookup`.
 * The backend returns per-key status/value items; this client normalizes them
 * into a simple `{ [key]: value | null }` map.
 *
 * Normalization rules:
 * - All requested keys are present in the returned object.
 * - Keys with non-"ok" status (or missing in the response) are returned as `null`.
 *
 * Error handling matches other API clients:
 * - Non-2xx responses throw `ApiError`.
 * - Network errors throw a plain `Error`.
 * - Aborted requests rethrow the `AbortError`.
 */

import type { LatLng, Param } from "../types/params";
import type { paths } from "./_generated/openapi.types";
import { ApiError, buildHttpErrorMessage, safeReadText } from "./apiError";

type LookupPath = paths["/api/local_params/lookup"];

type ParamLookupRequest = LookupPath["post"]["requestBody"]["content"]["application/json"];

type ParamLookupResponse = LookupPath["post"]["responses"]["200"]["content"]["application/json"];

export async function lookupLocalParams(args: {
  pos: LatLng;
  localParams: Param[];
  inputs?: ParamLookupRequest["inputs"];
  signal?: AbortSignal;
}): Promise<Record<string, number | string | null>> {
  /**
   * Request local (location-derived) parameter defaults for a coordinate.
   *
   * Returns a map for the requested keys; values are `number|string|null`.
   */
  const { pos, localParams: localParams, signal } = args;

  // Build backend request (typed from OpenAPI)
  const req: ParamLookupRequest = {
    location: { lat: pos.lat, lng: pos.lng },
    keys: localParams.map((p) => p.key),
    inputs: args.inputs,
  };

  // Initialize output with nulls for all requested keys
  const out: Record<string, number | string | null> = Object.fromEntries(
    localParams.map((p) => [p.key, null]),
  );

  const url = "/api/local_params/lookup";

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
    console.error("lookupLocalParams: HTTP error", resp.status, text);
    throw new ApiError({
      message: msg,
      status: resp.status,
      url,
      bodyText: text,
    });
  }

  const data = (await resp.json()) as ParamLookupResponse;

  // Map results to key->value; treat non-ok as null by default
  for (const r of data.results ?? []) {
    if (!(r.key in out)) continue;

    if (r.status === "ok") {
      // In your current contract, value can be number|string|null (and is optional)
      out[r.key] = (r.value ?? null) as number | string | null;
    } else {
      out[r.key] = null;
    }
  }

  return out;
}
