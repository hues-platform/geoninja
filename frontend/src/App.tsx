/**
 * Top-level application component.
 *
 * Responsibilities:
 * - Own the in-memory parameter registry state (seeded from the static `PARAMS` definition).
 * - Kick off async flows that depend on schema/marker state:
 *   - local parameter lookup (fills defaults for `paramType="local"`)
 *   - analysis run orchestration (handled by the `useAnalysisRunProcessing` hook)
 * - Render the main layout: map + control panel + results panel + global error toasts.
 *
 * Notes:
 * - The `PARAMS` object is treated as an immutable registry definition; we keep a stateful
 *   copy so user edits and fetched local defaults don’t mutate the constant.
 */
import "leaflet/dist/leaflet.css";
import { useMemo, useState } from "react";

import { ControlPanel } from "./components/control/ControlPanel";
import { ResultsPanel } from "./components/results/ResultsPanel";
import ErrorToasts from "./components/common/ErrorToasts";
import { selectParams } from "./config/paramSelectors";
import { PARAMS } from "./config/params";
import { validateAllParams } from "./config/paramValidation";
import Map from "./map/Map";
import { useAppStore } from "./process/appStore";
import { useAnalysisRunProcessing } from "./process/useAnalysisRunProcessing";
import { useParamLookupProcessing } from "./process/useParamLookupProcessing";
import type { AnalysisRunContext } from "./types/analysisRun";
import {
  type NumericParam,
  type ParamRegistry,
  type StringParam,
  getValidEffectiveInt,
} from "./types/params";

type ParamValue = number | string;

const APP_CONTAINER_STYLE: React.CSSProperties = {
  position: "relative",
  height: "100%",
  width: "100%",
};

function setParamValue(prev: ParamRegistry, key: string, value: ParamValue): ParamRegistry {
  const p = prev[key];
  if (!p) return prev;

  // Ignore edits for non-editable params
  if (!p.editable) return prev;

  if (p.valueType === "number") {
    if (typeof value !== "number") return prev;
    const updated: NumericParam = { ...p, value };
    return { ...prev, [key]: updated };
  }

  // p.valueType === "string"
  if (typeof value !== "string") return prev;
  const updated: StringParam = { ...p, value };
  return { ...prev, [key]: updated };
}

function applyLocalDefaultsToRegistry(
  prev: ParamRegistry,
  values: Record<string, ParamValue | null>,
): ParamRegistry {
  let next = prev;

  for (const [key, fetched] of Object.entries(values)) {
    const p = next[key];
    if (!p) continue;
    if (p.paramType !== "local") continue;

    if (p.valueType === "number") {
      if (fetched !== null && typeof fetched !== "number") continue;
      const updated: NumericParam = {
        ...p,
        default: fetched === null ? undefined : fetched,
        value: fetched === null ? undefined : fetched,
      };
      next = { ...next, [key]: updated };
      continue;
    }

    // p.valueType === "string"
    if (fetched !== null && typeof fetched !== "string") continue;
    const updated: StringParam = {
      ...p,
      default: fetched === null ? undefined : fetched,
      value: fetched === null ? undefined : fetched,
    };
    next = { ...next, [key]: updated };
  }

  return next;
}

function App() {
  // Keep a stateful copy because PARAMS is a constant registry
  const [params, setParams] = useState<ParamRegistry>(PARAMS);

  const onParamChange = (key: string, value: ParamValue) => {
    setParams((prev) => setParamValue(prev, key, value));
  };

  const applyLocalDefaults = (values: Record<string, ParamValue | null>) => {
    setParams((prev) => applyLocalDefaultsToRegistry(prev, values));
  };

  // For lookup schema (not impacted by current values)
  const localParamsSchema = useMemo(() => selectParams(PARAMS, "local"), []);

  const year = getValidEffectiveInt(params, "year");
  useParamLookupProcessing(localParamsSchema, applyLocalDefaults, year);
  console.log("Year for param lookup:", year);
  useAnalysisRunProcessing();

  // Parameter validation
  const validation = useMemo(() => validateAllParams(params), [params]);
  const allParamsValid = validation.allValid;
  const invalidStaticParamsCount = validation.invalidStaticKeys.length;
  const invalidLocalParamsCount = validation.invalidLocalKeys.length;

  // Analysis run and results panel
  const marker = useAppStore((state) => state.marker);
  const requestAnalysisRun = useAppStore((s) => s.requestAnalysisRun);
  const analysisRunContext = useAppStore((s) => s.analysisRun.context);
  const analysisRunRevision = useAppStore((s) => s.analysisRunRevision);
  const analysisResults = useAppStore((s) => s.analysisRun.results);
  const resetAnalysisRunOutcome = useAppStore((s) => s.resetAnalysisRunOutcome);
  const resultsOpen = analysisResults !== null;

  const onAnalysisRun = () => {
    if (!marker) return;

    const context: AnalysisRunContext = {
      id: analysisRunRevision + 1,
      startedAt: Date.now(),
      location: marker,
      params: structuredClone(params),
    };

    requestAnalysisRun(context);
  };

  // Build page
  return (
    <div style={APP_CONTAINER_STYLE}>
      <Map />
      <ErrorToasts />
      <ControlPanel
        params={params}
        validation={validation}
        onParamChange={onParamChange}
        allParamsValid={allParamsValid}
        invalidStaticParamsCount={invalidStaticParamsCount}
        invalidLocalParamsCount={invalidLocalParamsCount}
        onAnalysisRun={onAnalysisRun}
      />
      <ResultsPanel
        open={resultsOpen}
        context={analysisRunContext}
        results={analysisResults}
        onClose={resetAnalysisRunOutcome}
      />
    </div>
  );
}

export default App;
