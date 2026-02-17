/**
 * Contract sync test: parameter registry.
 *
 * Ensures the frontend parameter definition (`PARAMS`) matches the committed
 * shared contract file `contracts/params.json` for all contract-relevant fields.
 *
 * This prevents accidental drift between frontend forms, backend validation, and
 * the shared contract used across the repo.
 */

import { describe, expect, it } from "vitest";
import { PARAMS } from "./params";

import contract from "../../../contracts/params.json";
import type { Param } from "../types/params";

const contractSchemaVersion = 1;

type ContractParam = {
  key: string;
  paramType: string;
  valueType: string;
  unit: string | null;
  min: number | null;
  max: number | null;
  default: number | string | null;
};

type ContractFile = {
  schemaVersion: number;
  params: ContractParam[];
};

function normalizeFrontendParam(p: Param): ContractParam {
  if (p.valueType == "number") {
    return {
      key: p.key,
      paramType: p.paramType,
      valueType: p.valueType,
      unit: p.unit ?? null,
      min: p.min ?? null,
      max: p.max ?? null,
      default: p.default ?? null,
    };
  }

  return {
    key: p.key,
    paramType: p.paramType,
    valueType: p.valueType,
    unit: null,
    min: null,
    max: null,
    default: p.default ?? null,
  };
}

function normalizeContractParam(p: ContractParam): ContractParam {
  return {
    key: p.key,
    paramType: p.paramType,
    valueType: p.valueType,
    unit: p.unit ?? null,
    min: p.min ?? null,
    max: p.max ?? null,
    default: p.default ?? null,
  };
}

describe("params.ts mathces contracts/params.json", () => {
  it("has a 1:1 match on contract fields per key", () => {
    const contractFile = contract as unknown as ContractFile;

    expect(contractFile.schemaVersion).toBe(contractSchemaVersion);
    expect(Array.isArray(contractFile.params)).toBe(true);

    // Parameter lists from frontend and contract
    const frontendList = Object.values(PARAMS).map(normalizeFrontendParam);
    const contractList = contractFile.params.map(normalizeContractParam);

    // Key uniqueness checks
    const frontendKeys = frontendList.map((p) => p.key);
    const contractKeys = contractList.map((p) => p.key);
    expect(new Set(frontendKeys).size).toBe(frontendList.length);
    expect(new Set(contractKeys).size).toBe(contractList.length);

    // Key set must be identical
    expect(frontendKeys.slice().sort()).toEqual(contractKeys.slice().sort());

    // Compare relevant fields for each parameter
    frontendList.forEach((fp) => {
      const cp = contractList.find((c) => c.key === fp.key);
      expect(cp).toBeDefined();
      expect(fp).toEqual(cp);
    });
  });
});
