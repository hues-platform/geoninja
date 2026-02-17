/**
 * Parameter registry selectors.
 *
 * Small helpers that derive ordered param lists from the `ParamRegistry` map.
 * Ordering is controlled by the optional `order` field.
 */

import type { Param, ParamRegistry, ParamType } from "../types/params";

function sortByOrder(a: Param, b: Param) {
  return (a.order ?? 0) - (b.order ?? 0);
}

export function selectParams(registry: ParamRegistry, paramType: ParamType): Param[] {
  return Object.values(registry)
    .filter((p) => p.paramType == paramType)
    .slice()
    .sort(sortByOrder);
}
