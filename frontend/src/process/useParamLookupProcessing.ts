/**
 * Local parameter lookup processing hook.
 *
 * Watches marker changes (via `markerRevision`) and performs a backend lookup
 * for “local” parameter defaults for that location.
 *
 * Responsibilities:
 * - Abort any in-flight lookup when the marker changes.
 * - Call the local-param lookup endpoint.
 * - Apply returned values into the parameter registry via `applyLocalDefaults`.
 * - Update job lifecycle state in the app store and emit toast errors.
 */

import { useEffect } from "react";
import { useAppStore } from "./appStore";
import { lookupLocalParams } from "../api/localParamLookup";
import { ApiError } from "../api/apiError";
import { useErrorStore } from "./errorStore";
import type { Param } from "../types/params";

/**
 * Run local-parameter lookup whenever the marker changes.
 *
 * Parameters:
 * - `localParams`: the set of local parameters to request from the backend.
 * - `applyLocalDefaults`: called with a key→value map returned by the backend.
 *
 * Note: since this effect depends on `localParams` and `applyLocalDefaults`,
 * callers should keep those references stable when possible to avoid
 * unintended re-runs.
 */
export function useParamLookupProcessing(
  localParams: Param[],
  applyLocalDefaults: (values: Record<string, number | string | null>) => void,
  year?: number,
) {
  // Access map store state and actions
  const marker = useAppStore((state) => state.marker);
  const markerRevision = useAppStore((state) => state.markerRevision);

  // Actions to manage location-based parameter lookup job
  const startParamLookup = useAppStore((state) => state.startParamLookup);
  const finishParamLookup = useAppStore((state) => state.finishParamLookup);
  const failParamLookup = useAppStore((state) => state.failParamLookup);
  const abortParamLookup = useAppStore((state) => state.abortParamLookup);

  // Effect to trigger processing when marker changes
  useEffect(() => {
    // No marker, nothing to do
    if (!marker) return;

    // Abort any in-flight job immediately
    abortParamLookup();

    // Start new processing job
    const controller = new AbortController();
    startParamLookup(marker, controller);

    // Perform the processing asynchronously
    (async () => {
      // Prepare arguments for lookup call
      const lookupArgs: Parameters<typeof lookupLocalParams>[0] = {
        pos: marker,
        localParams,
        signal: controller.signal,
      };
      // Include inputs that are considered optional for the backend lookup
      const inputs: NonNullable<typeof lookupArgs.inputs> = {};
      if (year !== undefined) {
        inputs.year = year;
      }
      if (Object.keys(inputs).length > 0) {
        lookupArgs.inputs = inputs;
      }

      try {
        // Call processing function at marker location
        const values = await lookupLocalParams(lookupArgs);
        // Apply returned parameter values
        applyLocalDefaults(values);
        finishParamLookup();
      } catch (err) {
        // Handle processing error
        if (controller.signal.aborted) return;

        const msg =
          err instanceof ApiError ? err.message : err instanceof Error ? err.message : String(err);
        useErrorStore.getState().pushError(msg);
        failParamLookup(msg);
      }
    })();

    // Cleanup: abort if marker changes or component unmounts
    return () => controller.abort();
  }, [
    markerRevision,
    marker,
    year,
    localParams,
    applyLocalDefaults,
    abortParamLookup,
    startParamLookup,
    finishParamLookup,
    failParamLookup,
  ]);
}
