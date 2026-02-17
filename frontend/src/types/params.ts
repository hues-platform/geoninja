/**
 * Parameter domain types.
 *
 * The frontend represents parameters as a registry keyed by `Param.key`.
 * Parameters can be:
 * - `static`: user-editable/configured inputs
 * - `local`: values looked up from the backend for a specific location
 *
 * Each param may have:
 * - a `default` (baseline value), and/or
 * - a `value` (explicitly set value)
 */

/** Geographic coordinate in WGS84 degrees. */
export type LatLng = { lat: number; lng: number };

/** How a parameter’s value is sourced. */
export type ParamType = "static" | "local";

/** Shared fields across all parameter value types. */
export type ParamBase = {
  key: string;
  name: string;
  description?: string;
  paramType: ParamType;
  editable: boolean;
  order?: number;
};

export type NumericParam = ParamBase & {
  valueType: "number";
  unit: string;
  min: number;
  max: number;
  default?: number;
  value?: number;
  displayUnit?: string;
  displayScaleFactor?: number;
};

export type StringParam = ParamBase & {
  valueType: "string";
  default?: string;
  value?: string;
};

/** A parameter can be numeric or string-valued. */
export type Param = NumericParam | StringParam;

/** Keyed parameter registry used throughout the UI. */
export type ParamRegistry = Record<string, Param>;

/** Returns true when the parameter declares a default value. */
export function hasDefault(p: Param): boolean {
  return p.default !== undefined;
}

/**
 * Returns the value that should be treated as “currently in effect”.
 *
 * Precedence:
 * - `value` (explicit) wins
 * - otherwise `default`
 * - otherwise `undefined` (no effective value)
 */
export function getEffectiveValue(p: Param): number | string | undefined {
  if (p.value !== undefined) return p.value;
  return p.default;
}

/**
 * Returns true if the parameter is not at its default.
 *
 * Semantics:
 * - If a default exists: changed iff `value` differs from `default`.
 * - If no default exists: changed iff a value is set.
 */
export function isChangedFromDefault(p: Param): boolean {
  if (p.default !== undefined) return p.default !== getEffectiveValue(p);
  if (p.value !== undefined) return true;
  return false;
}

/** Returns the parameter by key, or undefined if not present. */
export function getParam(reg: ParamRegistry, key: string): Param | undefined {
  return reg[key];
}

/**
 * Returns the effective numeric value if present and within bounds.
 *
 * - Uses `getEffectiveValue` (value wins over default).
 * - Returns `undefined` if the param is missing, not numeric, not a number,
 *   not finite, or outside [min, max].
 */
export function getValidEffectiveNumber(reg: ParamRegistry, key: string): number | undefined {
  const p = reg[key];
  if (!p || p.valueType !== "number") return undefined;

  const eff = getEffectiveValue(p);
  if (typeof eff !== "number" || !Number.isFinite(eff)) return undefined;

  if (eff < p.min || eff > p.max) return undefined;
  return eff;
}

/**
 * Returns the effective integer numeric value if present and within bounds.
 * Useful for discrete numeric params like `year`.
 */
export function getValidEffectiveInt(reg: ParamRegistry, key: string): number | undefined {
  const v = getValidEffectiveNumber(reg, key);
  return v !== undefined && Number.isInteger(v) ? v : undefined;
}
