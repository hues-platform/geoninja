import { beforeEach, describe, expect, it, vi } from "vitest";
import type { AnalysisRunResultsVM } from "../types/analysisRun";

beforeEach(() => {
  vi.resetModules();
});

describe("useAppStore", () => {
  it("setMarker increments markerRevision and stores provenance", async () => {
    const { useAppStore } = await import("./appStore");
    expect(useAppStore.getState().markerRevision).toBe(0);

    useAppStore.getState().setMarker({ lat: 1, lng: 2 }, "mapClick");
    const st = useAppStore.getState();
    expect(st.marker).toEqual({ lat: 1, lng: 2 });
    expect(st.markerRevision).toBe(1);
    expect(st.lastMarkerChange?.source).toBe("mapClick");
    expect(st.lastMarkerChange?.pos).toEqual({ lat: 1, lng: 2 });
    expect(typeof st.lastMarkerChange?.at).toBe("number");
  });

  it("aborts previous controllers when starting new jobs", async () => {
    const { useAppStore } = await import("./appStore");

    const c1 = new AbortController();
    const c2 = new AbortController();
    const abortSpy = vi.spyOn(c1, "abort");

    useAppStore.getState().startParamLookup({ lat: 1, lng: 2 }, c1);
    useAppStore.getState().startParamLookup({ lat: 3, lng: 4 }, c2);
    expect(abortSpy).toHaveBeenCalledTimes(1);
  });

  it("analysis run outcome follows results.status", async () => {
    const { useAppStore } = await import("./appStore");

    const okResults: AnalysisRunResultsVM = {
      status: "ok",
      message: null,
      atesKpiResults: [],
      derivedQuantities: [],
    };

    useAppStore.getState().finishAnalysisRun(okResults);
    expect(useAppStore.getState().analysisRun.outcome).toBe("success");

    const errResults: AnalysisRunResultsVM = {
      status: "error",
      message: "bad",
      atesKpiResults: [],
      derivedQuantities: [],
    };

    useAppStore.getState().finishAnalysisRun(errResults);
    const st = useAppStore.getState();
    expect(st.analysisRun.outcome).toBe("error");
    expect(st.analysisRun.error).toBe("bad");
  });
});
