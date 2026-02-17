/**
 * Season period (heating/cooling) group validation.
 *
 * The app represents seasonal boundaries as strings in `DD.MM` (or `DD.MM.`)
 * format (e.g. `01.10.`). A period is defined by a start and end boundary and
 * is interpreted as a CLOSED interval: `[start, end]`.
 *
 * Periods may wrap across the year boundary (e.g. `01.11` → `01.03`). To reason
 * about overlap on a circular domain (the year), we map wrapped ranges into a
 * linear interval on `[1..2N]` and test for overlap with shifted copies.
 *
 * This module performs cross-field validation only. Per-field validation
 * (required/format checks for individual strings) is handled elsewhere.
 */

import { getEffectiveValue, type Param } from "../../types/params";

export type GroupIssue = {
  severity: "error" | "warning";
  message: string;
  keys?: string[];
};

/**
 * Read an effective (value-or-default) non-empty string from a param list.
 *
 * Returns `null` if the key is missing, not a string param, or blank.
 */
function getString(params: Param[], key: string): string | null {
  const p = params.find((x) => x.key === key);
  if (!p || p.valueType !== "string") return null;

  const v = getEffectiveValue(p);
  if (typeof v !== "string") return null;

  const s = v.trim();
  return s.length > 0 ? s : null;
}

/**
 * Read an effective (value-or-default) finite number from a param list.
 *
 * Returns `null` if the key is missing, not a numeric param, or not finite.
 */
function getNumber(params: Param[], key: string): number | null {
  const p = params.find((x) => x.key === key);
  if (!p || p.valueType !== "number") return null;

  const v = getEffectiveValue(p);
  return typeof v === "number" && Number.isFinite(v) ? v : null;
}

/**
 * Parse a season boundary string in the format `DD.MM` or `DD.MM.`.
 */
function parseDDMM(raw: string): { day: number; month: number } | null {
  const m = raw.trim().match(/^([0-3]\d)\.([0-1]\d)\.?$/);
  if (!m) return null;

  const day = Number(m[1]);
  const month = Number(m[2]);

  if (day < 1 || day > 31) return null;
  if (month < 1 || month > 12) return null;

  return { day, month };
}

function isLeapYear(y: number): boolean {
  return (y % 4 === 0 && y % 100 !== 0) || y % 400 === 0;
}

/**
 * Convert a calendar date to day-of-year (1..365/366).
 *
 * Returns `null` if the date is invalid for the given year.
 */
function dayOfYear(year: number, month: number, day: number): number | null {
  const dim = [31, isLeapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];

  const maxDay = dim[month - 1];
  if (!maxDay) return null;
  if (day < 1 || day > maxDay) return null;

  let doy = 0;
  for (let i = 0; i < month - 1; i++) doy += dim[i]!;
  return doy + day;
}

type Interval = { a: number; b: number }; // [a,b] closed

/**
 * Convert circular closed interval `[start,end]` into linear `[a,b]` on `[1..2N]`.
 */
function toInterval(startDay: number, endDay: number, yearDays: number): Interval {
  if (endDay >= startDay) {
    return { a: startDay, b: endDay };
  }
  // wrap across year boundary
  return { a: startDay, b: yearDays + endDay };
}

/**
 * Closed-interval overlap check for linear intervals.
 */
function overlaps(x: Interval, y: Interval): boolean {
  return Math.max(x.a, y.a) <= Math.min(x.b, y.b);
}

/**
 * Check overlap on a circular year by testing shifted copies of `y`.
 */
function overlapsOnCircle(x: Interval, y: Interval, yearDays: number): boolean {
  if (overlaps(x, y)) return true;
  if (overlaps(x, { a: y.a + yearDays, b: y.b + yearDays })) return true;
  if (overlaps(x, { a: y.a - yearDays, b: y.b - yearDays })) return true;
  return false;
}

/**
 * Group-level validation for season definitions.
 *
 * Intervals are interpreted as CLOSED: [start, end]
 */
export function validateSeasonPeriods(params: Param[]): GroupIssue[] {
  const issues: GroupIssue[] = [];

  const year = getNumber(params, "year");
  if (year == null) return issues;

  const hsRaw = getString(params, "heatPeriodStart");
  const heRaw = getString(params, "heatPeriodEnd");
  const csRaw = getString(params, "coolPeriodStart");
  const ceRaw = getString(params, "coolPeriodEnd");

  // Stay quiet while user is mid-entry
  if (!hsRaw || !heRaw || !csRaw || !ceRaw) return issues;

  const hs = parseDDMM(hsRaw);
  const he = parseDDMM(heRaw);
  const cs = parseDDMM(csRaw);
  const ce = parseDDMM(ceRaw);

  // Format errors handled per-field
  if (!hs || !he || !cs || !ce) return issues;

  const hsD = dayOfYear(year, hs.month, hs.day);
  const heD = dayOfYear(year, he.month, he.day);
  const csD = dayOfYear(year, cs.month, cs.day);
  const ceD = dayOfYear(year, ce.month, ce.day);

  // Invalid calendar dates handled per-field
  if ([hsD, heD, csD, ceD].some((v) => v == null)) return issues;

  const yearDays = isLeapYear(year) ? 366 : 365;

  const heat = toInterval(hsD!, heD!, yearDays);
  const cool = toInterval(csD!, ceD!, yearDays);

  if (overlapsOnCircle(heat, cool, yearDays)) {
    issues.push({
      severity: "error",
      message:
        "Heating and cooling periods overlap. Adjust the start/end dates so the intervals do not intersect.",
      keys: ["heatPeriodStart", "heatPeriodEnd", "coolPeriodStart", "coolPeriodEnd"],
    });
  }

  return issues;
}
