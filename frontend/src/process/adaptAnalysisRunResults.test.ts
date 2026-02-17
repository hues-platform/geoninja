import { describe, expect, it } from "vitest";

import { adaptAnalysisRunResults } from "./adaptAnalysisRunResults";
import type { components } from "../api/_generated/openapi.types";

type AnalysisRunResultsDTO = components["schemas"]["AnalysisRunResults"];

describe("adaptAnalysisRunResults", () => {
  it("returns null for nullish input", () => {
    expect(adaptAnalysisRunResults(null)).toBeNull();
    expect(adaptAnalysisRunResults(undefined)).toBeNull();
  });

  it("normalizes missing fields to VM defaults", () => {
    const dto = { status: "ok" } as unknown as AnalysisRunResultsDTO;
    const vm = adaptAnalysisRunResults(dto);
    expect(vm).toEqual({
      atesKpiResults: [],
      derivedQuantities: [],
      status: "ok",
      message: null,
    });
  });

  it("maps items and normalizes value/unit to null", () => {
    const dto = {
      status: "error",
      message: "msg",
      ates_kpi_results: [{ key: "a", value: undefined, unit: undefined }],
      derived_quantities: [{ key: "b", value: 3.14, unit: "m" }],
    } as unknown as AnalysisRunResultsDTO;

    const vm = adaptAnalysisRunResults(dto);

    expect(vm?.status).toBe("error");
    expect(vm?.message).toBe("msg");
    expect(vm?.atesKpiResults).toEqual([{ key: "a", value: null, unit: null }]);
    expect(vm?.derivedQuantities).toEqual([{ key: "b", value: 3.14, unit: "m" }]);
  });
});
