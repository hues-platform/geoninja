import { describe, expect, it } from "vitest";

import { validateAllParams, validateParam } from "./paramValidation";
import type { Param, ParamRegistry } from "../types/params";

describe("validateParam", () => {
  it("treats non-editable params as valid", () => {
    const p: Param = {
      key: "x",
      name: "x",
      paramType: "local",
      editable: false,
      valueType: "string",
    };
    expect(validateParam(p).isValid).toBe(true);
  });

  it("validates numeric bounds", () => {
    const p: Param = {
      key: "n",
      name: "n",
      paramType: "static",
      editable: true,
      valueType: "number",
      unit: "-",
      min: 0,
      max: 10,
      default: 5,
      value: 11,
    };
    const v = validateParam(p);
    expect(v.isValid).toBe(false);
    expect(v.reason).toContain("maximum");
  });

  it("validates season boundary date format for specific keys", () => {
    const p: Param = {
      key: "heatPeriodStart",
      name: "heatPeriodStart",
      paramType: "static",
      editable: true,
      valueType: "string",
      value: "2020-10-01",
    };
    const v = validateParam(p);
    expect(v.isValid).toBe(false);
    expect(v.reason).toContain("DD.MM");
  });
});

describe("validateAllParams", () => {
  it("adds group-level error when heating and cooling overlap", () => {
    const reg: ParamRegistry = {
      year: {
        key: "year",
        name: "year",
        paramType: "static",
        editable: true,
        valueType: "number",
        unit: "-",
        min: 1990,
        max: 2100,
        default: 2020,
      },
      heatPeriodStart: {
        key: "heatPeriodStart",
        name: "heatPeriodStart",
        paramType: "static",
        editable: true,
        valueType: "string",
        value: "01.10.",
      },
      heatPeriodEnd: {
        key: "heatPeriodEnd",
        name: "heatPeriodEnd",
        paramType: "static",
        editable: true,
        valueType: "string",
        value: "01.03.",
      },
      coolPeriodStart: {
        key: "coolPeriodStart",
        name: "coolPeriodStart",
        paramType: "static",
        editable: true,
        valueType: "string",
        value: "01.02.",
      },
      coolPeriodEnd: {
        key: "coolPeriodEnd",
        name: "coolPeriodEnd",
        paramType: "static",
        editable: true,
        valueType: "string",
        value: "01.06.",
      },
    };

    const summary = validateAllParams(reg);
    expect(summary.allValid).toBe(false);
    for (const k of ["heatPeriodStart", "heatPeriodEnd", "coolPeriodStart", "coolPeriodEnd"]) {
      expect(summary.validityByKey[k]?.isValid).toBe(false);
      expect(summary.validityByKey[k]?.reason).toContain("overlap");
    }
  });
});
