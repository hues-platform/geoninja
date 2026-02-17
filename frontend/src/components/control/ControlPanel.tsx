/**
 * Control panel sidebar.
 *
 * This component renders the primary UI for:
 * - selecting a location (search text or coordinate input)
 * - editing static (location-independent) parameters
 * - viewing/editing local (location-derived) parameters via a popup
 * - triggering an analysis run
 *
 * It is intentionally “dumb” about async workflows: it receives parameter state
 * and validation from the parent (`App`), and it reads only minimal UI flags
 * from the app store (marker presence, lookup active, analysis active).
 */
import { useMemo, useState, type CSSProperties } from "react";
import { useAppStore } from "../../process/appStore";
import type { ParamRegistry } from "../../types/params";
import { selectParams } from "../../config/paramSelectors";
import type { ValidationSummary } from "../../config/paramValidation";
import { ParamField } from "./ParamField";
import LocationSearchBar from "../location/LocationSearchBar";
import CoordinateNavigator from "../location/CoordinateNavigator";
import LocalParamsPopup from "./LocalParamsPopup";

type ControlPanelProps = {
  /** Full parameter registry (static + local), including current values/defaults. */
  params: ParamRegistry;

  /** Validation results for the current parameter registry. */
  validation: ValidationSummary;

  /** Called when a user edits a parameter field in this panel or popup. */
  onParamChange: (key: string, value: number | string) => void;

  /** Convenience flag: all parameters currently validate. */
  allParamsValid: boolean;

  /** Number of invalid static (location-independent) parameter fields. */
  invalidStaticParamsCount: number;

  /** Number of invalid local (location-derived) parameter fields. */
  invalidLocalParamsCount: number;

  /** Called when the user presses “Run Analysis”. */
  onAnalysisRun: () => void;
};

export function ControlPanel({
  params,
  validation,
  onParamChange,
  allParamsValid,
  invalidStaticParamsCount,
  invalidLocalParamsCount,
  onAnalysisRun,
}: ControlPanelProps) {
  // State for local parameters popup
  const [localParamsOpen, setLocalParamsOpen] = useState(false);

  // Obtain static and local params from registry
  const staticParams = useMemo(() => selectParams(params, "static"), [params]);
  const localParams = useMemo(() => selectParams(params, "local"), [params]);
  const allParams = useMemo(() => Object.values(params), [params]);

  // Check if a marker is set on the map
  const marker = useAppStore((state) => state.marker);
  const setMarker = useAppStore((state) => state.setMarker);
  const hasLocation = marker !== null;

  // Check if parameters are currently being gathered
  const paramLookupActive = useAppStore((s) => s.paramLookup.active);
  const canOpenLocalParams = hasLocation && !paramLookupActive;

  // Analysis run processing
  const analysisRunActive = useAppStore((s) => s.analysisRun.active);
  const canRun = hasLocation && !analysisRunActive && allParamsValid;

  // Build the control panel
  return (
    <div
      style={{
        position: "absolute",
        top: 12,
        left: 12,
        width: 200,

        maxHeight: "calc(100vh - 24px)",
        overflowY: "auto",

        background: "white",
        padding: 12,
        borderRadius: 8,
        boxShadow: "0 2px 12px rgba(0,0,0,0.15)",

        zIndex: 1000,
      }}
    >
      {/* Location search bar */}
      <LocationSearchBar onSelect={(pos) => setMarker(pos, "searchText")} />
      {/* Coordinate navigator */}
      <CoordinateNavigator onGo={(lat, lon) => setMarker({ lat: lat, lng: lon }, "searchCoords")} />

      {/* Local parameters popup button */}
      <button
        type="button"
        disabled={!canOpenLocalParams}
        onClick={() => {
          if (!canOpenLocalParams) return;
          setLocalParamsOpen(true);
        }}
        style={{
          ...styles.localParamsBtn,
          ...(canOpenLocalParams ? styles.localParamsBtnActive : styles.localParamsBtnDisabled),
        }}
      >
        {paramLookupActive ? "Loading..." : "Local parameters"}
      </button>
      {/* Local parameters validity indicator */}
      {!paramLookupActive && invalidLocalParamsCount > 0 && hasLocation && (
        <div style={styles.paramWarning}>
          {invalidLocalParamsCount} invalid local parameter
          {invalidLocalParamsCount > 1 ? "s" : ""}
        </div>
      )}

      {/* Local parameters popup */}
      <LocalParamsPopup
        isOpen={localParamsOpen}
        localParams={localParams}
        validationParams={allParams}
        validityByKey={validation.validityByKey}
        onClose={() => setLocalParamsOpen(false)}
        onParamChange={onParamChange}
      />

      {/* Static (location-independent) parameters */}
      {staticParams.map((p) => (
        <ParamField
          key={p.key}
          param={p}
          onChange={onParamChange}
          validity={validation.validityByKey[p.key]}
        />
      ))}
      {/* Static parameters validity indicator */}
      {invalidStaticParamsCount > 0 && (
        <div style={styles.paramWarning}>
          {invalidStaticParamsCount} invalid static parameter
          {invalidStaticParamsCount > 1 ? "s" : ""}
        </div>
      )}

      {/* Run button */}
      <button
        type="button"
        disabled={!canRun}
        onClick={onAnalysisRun}
        style={{
          ...styles.runBtn,
          ...(canRun ? styles.runBtnActive : styles.runBtnDisabled),
        }}
      >
        {analysisRunActive ? "Running…" : "Run Analysis"}
      </button>
    </div>
  );
}

const styles: Record<string, CSSProperties> = {
  localParamsBtn: {
    width: "100%",
    marginBottom: 12,
    padding: "8px 0px",
    borderRadius: 4,
    fontSize: 10,
    fontWeight: 600,
    border: "1px solid transparent",
  },

  localParamsBtnActive: {
    background: "#1e6bd6",
    borderColor: "#1e6bd6",
    color: "#ffffff",
    cursor: "pointer",
    boxShadow: "0 0 0 1px rgba(30,107,214,0.15)",
  },

  localParamsBtnDisabled: {
    background: "#f2f2f2",
    borderColor: "rgba(0,0,0,0.2)",
    color: "rgba(0,0,0,0.45)",
    cursor: "not-allowed",
  },

  runBtn: {
    width: "100%",
    marginTop: 12,
    padding: "8px 0px",
    borderRadius: 4,
    fontSize: 11,
    fontWeight: 700,
    border: "1px solid transparent",
  },

  runBtnActive: {
    background: "#1e6bd6",
    borderColor: "#1e6bd6",
    color: "#ffffff",
    cursor: "pointer",
  },

  runBtnDisabled: {
    background: "#f2f2f2",
    borderColor: "rgba(0,0,0,0.2)",
    color: "rgba(0,0,0,0.45)",
    cursor: "not-allowed",
  },

  paramWarning: {
    marginTop: -6,
    marginBottom: 10,
    fontSize: 10,
    fontWeight: 600,
    color: "#b42318",
    textAlign: "center",
  },
};
