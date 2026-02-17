/**
 * Analysis-run processing hook.
 *
 * The UI requests an analysis by calling `useAppStore.getState().requestAnalysisRun(context)`.
 * That increments `analysisRunRevision`, which this hook observes.
 *
 * Responsibilities:
 * - Read the latest run context from the store at execution time.
 * - Abort any previous run before starting a new one.
 * - Call the API, adapt DTO → VM, and update the store with success/failure.
 * - Push a user-visible error toast on failures.
 */

import { useEffect } from "react";
import { useAppStore } from "./appStore";
import { useErrorStore } from "./errorStore";
import { runAnalysis } from "../api/analysisRun";
import { adaptAnalysisRunResults } from "./adaptAnalysisRunResults";

export function useAnalysisRunProcessing() {
  const analysisRunRevision = useAppStore((s) => s.analysisRunRevision);
  const startAnalysisRun = useAppStore((s) => s.startAnalysisRun);
  const finishAnalysisRun = useAppStore((s) => s.finishAnalysisRun);
  const failAnalysisRun = useAppStore((s) => s.failAnalysisRun);
  const abortAnalysisRun = useAppStore((s) => s.abortAnalysisRun);

  useEffect(() => {
    // Don't run on initial mount
    if (analysisRunRevision === 0) return;

    const pushError = useErrorStore.getState().pushError;

    // Read the latest marker at run-time (do not re-trigger on marker changes)
    const context = useAppStore.getState().analysisRun.context;
    if (!context) {
      const msg = "Missing run context.";
      failAnalysisRun(msg);
      pushError(msg);
      return;
    }

    // Abort previous run defensively
    abortAnalysisRun();

    // Create a new abort controller for this run
    const controller = new AbortController();
    startAnalysisRun(context.location, controller);

    (async () => {
      try {
        const resp = await runAnalysis({
          pos: context.location,
          params: context.params,
          runId: context.id,
          startedAt: context.startedAt,
          signal: controller.signal,
        });
        const vm = adaptAnalysisRunResults(resp.results);
        if (!vm) {
          const msg = "Analysis run returned no results.";
          failAnalysisRun(msg);
          pushError(msg);
          return;
        }
        finishAnalysisRun(vm);
      } catch (e) {
        if (controller.signal.aborted) return;
        const msg = e instanceof Error ? e.message : String(e);
        failAnalysisRun(msg);
        pushError(msg);
      }
    })();

    return () => {
      abortAnalysisRun();
    };
  }, [analysisRunRevision, startAnalysisRun, finishAnalysisRun, failAnalysisRun, abortAnalysisRun]);
}
