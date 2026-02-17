/**
 * AppState
 * --------
 * Central application store for GeoNinja.
 *
 * It is explicitly responsible for:
 *
 *   1) The currently selected location (marker) and its provenance
 *   2) Async workflows that are *driven by the selected location*
 *      - parameter lookup
 *      - analysis run
 *
 * The store acts as a domain-level state machine for
 * "location → workflows → results".
 *
 * It is NOT a generic "global state" bucket.
 *
 * Side effects (fetching, cancellation, retries) should live in
 * `src/process/*` hooks; this store holds state and intent only.
 *
 * Implementation note:
 * - The store holds the current AbortController for each job so starting a new
 *   job can defensively abort any previous in-flight request.
 */

import { create } from "zustand";
import type { LatLng } from "../types/params";
import type { AnalysisRunContext, AnalysisRunResultsVM } from "../types/analysisRun";

// Source of location change events
export type LocationChangeSource = "mapClick" | "searchText" | "searchCoords" | "other";

/**
 * AppState
 * --------
 * Central application state for GeoNinja.
 *
 * AppState captures the domain state around the currently selected
 * geographic location and the workflows that are driven by that selection.
 *
 * It contains:
 *   - the active location (marker) and metadata about how/when it changed
 *   - lifecycle state for location-based async workflows
 *       • parameter lookup
 *       • analysis run
 *   - results and outcomes of those workflows for UI consumption
 *
 * AppState is intentionally focused on "location → workflows → results".
 * UI-only state, map rendering internals, and unrelated application settings
 * are expected to live outside this store.
 */
type AppState = {
  // Selection
  marker: LatLng | null;
  setMarker: (pos: LatLng, source?: LocationChangeSource) => void;

  // Marker memory
  markerRevision: number;
  lastMarkerChange: {
    pos: LatLng;
    source: LocationChangeSource;
    at: number;
  } | null;

  // Parameter lookup
  paramLookup: JobState;
  startParamLookup: (pos: LatLng, controller: AbortController) => void;
  finishParamLookup: () => void;
  failParamLookup: (msg: string) => void;
  abortParamLookup: () => void;

  // Analysis Run
  analysisRun: AnalysisRunState;
  analysisRunRevision: number;
  requestAnalysisRun: (context: AnalysisRunContext) => void;
  startAnalysisRun: (pos: LatLng, controller: AbortController) => void;
  finishAnalysisRun: (results: AnalysisRunResultsVM) => void;
  failAnalysisRun: (msg: string) => void;
  abortAnalysisRun: () => void;
  resetAnalysisRunOutcome: () => void;
};

export const useAppStore = create<AppState>((set, get) => ({
  // ---------------------------------------------------------------------------
  // Location selection
  // ---------------------------------------------------------------------------
  marker: null, // Represents the currently selected geographic location.
  setMarker: (marker, source = "other") =>
    /**
     * Set the active location marker.
     *
     * The optional `source` captures *how* the location was changed
     * (map click, search, etc.) and is used to drive downstream behavior
     * (e.g. camera jumps, auto-lookups, UX decisions).
     *
     * This function is the single entry point for all location changes.
     */
    set((state) => ({
      marker,
      markerRevision: state.markerRevision + 1,
      lastMarkerChange: {
        pos: marker,
        source,
        at: Date.now(),
      },
    })),

  // ---------------------------------------------------------------------------
  // Marker change metadata
  // ---------------------------------------------------------------------------
  // Used to detect and react to location changes in effect hooks.
  markerRevision: 0, // acts as an event counter
  lastMarkerChange: null, // captures provenance and timing for richer reactions.

  // ---------------------------------------------------------------------------
  // Parameter lookup workflow
  // ---------------------------------------------------------------------------
  // Tracks the lifecycle of the location-based parameter lookup request.
  paramLookup: {
    active: false,
    forPos: null,
    error: null,
    outcome: "idle",
    _abortController: null,
  },

  startParamLookup: (pos, controller) => {
    /**
     * Start a parameter lookup for the given location.
     * Any in-flight lookup is aborted before starting a new one.
     */
    const prev = get().paramLookup._abortController;
    abortIfPresent(prev);
    set((state) => ({
      paramLookup: {
        ...state.paramLookup,
        active: true,
        forPos: pos,
        error: null,
        outcome: "idle",
        _abortController: controller,
      },
    }));
  },

  finishParamLookup: () => {
    /**
     * Mark the parameter lookup as successfully completed.
     */
    set((state) => ({
      paramLookup: {
        ...state.paramLookup,
        active: false,
        forPos: null,
        outcome: "success",
        _abortController: null,
      },
    }));
  },

  failParamLookup: (msg) => {
    /**
     * Mark the parameter lookup as failed with an error message.
     */
    set((state) => ({
      paramLookup: {
        ...state.paramLookup,
        active: false,
        error: msg,
        outcome: "error",
        _abortController: null,
      },
    }));
  },

  abortParamLookup: () => {
    /**
     * Abort any in-flight parameter lookup and reset its state.
     */
    const prev = get().paramLookup._abortController;
    abortIfPresent(prev);
    set((state) => ({
      paramLookup: {
        ...state.paramLookup,
        active: false,
        forPos: null,
        outcome: "idle",
        _abortController: null,
      },
    }));
  },

  // ---------------------------------------------------------------------------
  // Analysis run workflow
  // ---------------------------------------------------------------------------
  // Tracks the lifecycle and results of the analysis run triggered by clicking
  // "Run" for the currently selected location.
  //
  // Execution is triggered indirectly via `requestAnalysisRun`,
  // allowing effects to react declaratively.
  analysisRun: {
    active: false,
    forPos: null,
    error: null,
    outcome: "idle",
    context: null,
    results: null,
    _abortController: null,
  },
  analysisRunRevision: 0,

  requestAnalysisRun: (context) => {
    /**
     * Request an analysis run for the current location.
     *
     * This function does NOT execute the run directly.
     * It records intent + context and bumps `analysisRunRevision`,
     * which effect hooks observe to perform the actual async work.
     */
    set((state) => ({
      analysisRun: {
        ...state.analysisRun,
        context: context,
        outcome: "idle",
        results: null,
        error: null,
      },
      analysisRunRevision: state.analysisRunRevision + 1,
    }));
  },
  startAnalysisRun: (pos, controller) => {
    /**
     * Start an analysis run for the given location.
     * Any in-flight run is aborted before starting a new one.
     */
    const prev = get().analysisRun._abortController;
    abortIfPresent(prev);

    set((state) => ({
      analysisRun: {
        ...state.analysisRun,
        active: true,
        forPos: pos,
        error: null,
        outcome: "idle",
        results: null,
        _abortController: controller,
      },
    }));
  },
  finishAnalysisRun: (results) => {
    /**
     * Mark the analysis run as successfully completed.
     */
    set((state) => ({
      analysisRun: {
        ...state.analysisRun,
        active: false,
        forPos: null,
        results: results,
        error: results.message ?? null,
        outcome: results.status === "ok" ? "success" : "error",
        _abortController: null,
      },
    }));
  },
  failAnalysisRun: (msg) => {
    /**
     * Mark the analysis run as failed with an error message.
     */
    set((state) => ({
      analysisRun: {
        ...state.analysisRun,
        active: false,
        error: msg,
        outcome: "error",
        results: null,
        _abortController: null,
      },
    }));
  },
  abortAnalysisRun: () => {
    /**
     * Abort any in-flight analysis run and reset its state.
     */
    const prev = get().analysisRun._abortController;
    abortIfPresent(prev);
    set((state) => ({
      analysisRun: {
        ...state.analysisRun,
        active: false,
        forPos: null,
        outcome: "idle",
        results: null,
        _abortController: null,
      },
    }));
  },
  resetAnalysisRunOutcome: () => {
    /**
     * Reset the analysis run outcome and results.
     * Does not abort any in-flight run.
     */
    set((state) => ({
      analysisRun: {
        ...state.analysisRun,
        outcome: "idle",
        context: null,
        results: null,
        error: null,
      },
    }));
  },
}));

/**
 * JobOutcome
 * ----------
 * Coarse-grained UI-facing outcome of an async workflow.
 *
 * - "idle": no completed outcome to show (initial state, aborted, or reset)
 * - "success": last completed run finished successfully
 * - "error": last completed run failed (error message available)
 *
 * Note: `active` indicates an in-flight request; `outcome` describes the last
 * terminal result (or lack thereof) that the UI may want to present.
 */
type JobOutcome = "idle" | "success" | "error";

// Common lifecycle state for a location-driven async job.
type JobState = {
  active: boolean;
  forPos: LatLng | null;
  error: string | null;
  outcome: JobOutcome;
  _abortController: AbortController | null;
};

/**
 * AnalysisRunState
 * ---------------
 * Extends JobState with analysis-specific payload.
 *
 * - context: captured run inputs (static params, local params, etc.)
 *            as requested by the user (set by `requestAnalysisRun`)
 * - results: backend response payload for the last completed run
 *
 * Separation of concern:
 * - `requestAnalysisRun(context)` records intent + inputs.
 * - `start/finish/fail/abort` manages lifecycle and results.
 */
type AnalysisRunState = JobState & {
  context: AnalysisRunContext | null;
  results: AnalysisRunResultsVM | null;
};

// Abort the given AbortController if it is non-null.
function abortIfPresent(c: AbortController | null) {
  if (c) c.abort();
}
