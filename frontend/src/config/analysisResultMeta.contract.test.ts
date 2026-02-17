/**
 * Contract sync test: analysis result metadata.
 *
 * Ensures the frontend UI metadata (`ANALYSIS_RESULT_META`) matches the committed
 * contract file `contracts/analysis_results.json`:
 * - every contract key has a meta entry (coverage)
 * - there are no extra meta keys not present in the contract
 * - entries are internally consistent (meta.key matches map key, names non-empty)
 */

import { describe, expect, it } from "vitest";
import contract from "../../../contracts/analysis_results.json";
import { ANALYSIS_RESULT_META } from "./analysisResultMeta";

type Contract = {
  derived_quantities: Array<{ key: string; unit: string }>;
  ates_kpi_results: Array<{ key: string; unit: string }>;
};

function contractKeys(c: Contract): string[] {
  return [...c.derived_quantities, ...c.ates_kpi_results].map((e) => e.key);
}

describe("analysis result meta contract", () => {
  it("covers all analysis result keys from contract", () => {
    const keys = contractKeys(contract as Contract);

    const missing = keys.filter((k) => !(k in ANALYSIS_RESULT_META));
    expect(missing, `Missing keys in ANALYSIS_RESULT_META: ${missing.join(", ")}`).toEqual([]);
  });

  it("does not contain keys that are not in the contract", () => {
    const keys = new Set(contractKeys(contract as Contract));

    const extra = Object.keys(ANALYSIS_RESULT_META).filter((k) => !keys.has(k));
    expect(
      extra,
      `Extra keys in ANALYSIS_RESULT_META not in contract: ${extra.join(", ")}`,
    ).toEqual([]);
  });

  it("has internally consistent entries", () => {
    for (const [k, meta] of Object.entries(ANALYSIS_RESULT_META)) {
      expect(meta.key, `Meta entry key mismatch for "${k}"`).toBe(k);
      expect(meta.name, `Meta entry "${k}" must have a non-empty name`).toBeTruthy();
      // description/order are optional; no assertions needed
    }
  });
});
