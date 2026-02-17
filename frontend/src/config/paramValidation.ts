/**
 * Parameter validation.
 *
 * This module provides:
 * - per-field validation (`validateParam`) based on type, requiredness, and numeric bounds
 * - aggregate validation (`validateAllParams`) that combines per-field results with
 *   cross-field/group constraints (currently: heating/cooling season periods)
 *
 * The UI uses the returned `ValidationSummary` to disable “Run Analysis” and to
 * highlight invalid fields.
 */

import type { Param, NumericParam, StringParam, ParamRegistry } from "../types/params";
import { validateSeasonPeriods } from "../components/control/seasonValidation";

export type ParamValidity = {
  isValid: boolean;
  reason?: string;
};

export type ValidationSummary = {
  validityByKey: Record<string, ParamValidity>;
  allValid: boolean;
  invalidKeys: string[];
  invalidStaticKeys: string[];
  invalidLocalKeys: string[];
};

export function validateParam(p: Param): ParamValidity {
  /**
   * Validate a single parameter value.
   *
   * For non-editable params we currently return valid (they are populated via
   * location lookup or represent derived/non-user-entered values).
   */
  if (!p.editable) return { isValid: true };

  if (p.valueType === "number") {
    const pn = p as NumericParam;
    const val = pn.value ?? pn.default;

    if (val === undefined || val === null) return { isValid: false, reason: "Missing value" };
    if (!Number.isFinite(val)) return { isValid: false, reason: "Not a finite number" };
    if (pn.min !== undefined && val < pn.min)
      return { isValid: false, reason: `Value below minimum of ${pn.min}` };
    if (pn.max !== undefined && val > pn.max)
      return { isValid: false, reason: `Value above maximum of ${pn.max}` };

    return { isValid: true };
  }

  // String value
  const ps = p as StringParam;
  const val = ps.value ?? ps.default;

  if (val === undefined || val === null) return { isValid: false, reason: "Missing value" };
  if (typeof val !== "string") return { isValid: false, reason: "Not a string" };
  if (val.trim().length === 0) return { isValid: false, reason: "Empty string" };

  // Key-specific validation for season boundary dates
  if (SEASON_DATE_KEYS.has(p.key)) {
    if (!isValidDDMM(val)) {
      return { isValid: false, reason: "Invalid date format. Use DD.MM. (e.g., 01.10.)" };
    }
  }

  return { isValid: true };
}

export function validateAllParams(reg: ParamRegistry): ValidationSummary {
  /**
   * Validate the entire registry.
   *
   * In addition to per-field checks, this applies group-level validation and
   * maps group issues back onto the relevant keys.
   */
  const validityByKey: Record<string, ParamValidity> = {};
  const invalidKeys: string[] = [];
  const invalidStaticKeys: string[] = [];
  const invalidLocalKeys: string[] = [];

  // Per-field validation
  for (const [key, p] of Object.entries(reg)) {
    const validity = validateParam(p);
    validityByKey[key] = validity;

    if (!validity.isValid) {
      invalidKeys.push(key);
      if (p.paramType === "static") invalidStaticKeys.push(key);
      if (p.paramType === "local") invalidLocalKeys.push(key);
    }
  }

  // Group-level validation
  const seasonIssues = validateSeasonPeriods(Object.values(reg));
  const seasonErrorIssues = seasonIssues.filter((i) => i.severity === "error");
  if (seasonErrorIssues.length > 0) {
    const alreadyInvalid = new Set(invalidKeys);
    for (const issue of seasonErrorIssues) {
      for (const key of issue.keys ?? []) {
        const p = reg[key];
        if (!p) continue;
        validityByKey[key] = {
          isValid: false,
          reason: issue.message,
        };
        if (!alreadyInvalid.has(key)) {
          alreadyInvalid.add(key);
          invalidKeys.push(key);
          if (p.paramType === "static") invalidStaticKeys.push(key);
          if (p.paramType === "local") invalidLocalKeys.push(key);
        }
      }
    }
  }

  return {
    validityByKey,
    allValid: invalidKeys.length === 0,
    invalidKeys,
    invalidStaticKeys,
    invalidLocalKeys: invalidLocalKeys,
  };
}

const SEASON_DATE_KEYS = new Set([
  "heatPeriodStart",
  "heatPeriodEnd",
  "coolPeriodStart",
  "coolPeriodEnd",
]);

function isValidDDMM(val: string): boolean {
  // Accept "DD.MM" or "DD.MM."
  const m = val.trim().match(/^([0-3]\d)\.([0-1]\d)\.?$/);
  if (!m) return false;

  const day = Number(m[1]);
  const month = Number(m[2]);

  if (day < 1 || day > 31) return false;
  if (month < 1 || month > 12) return false;

  return true;
}
