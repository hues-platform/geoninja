/**
 * Frontend parameter registry.
 *
 * `PARAMS` defines the parameter fields shown in the UI, including display
 * labels, descriptions, units, bounds, and defaults.
 *
 * Contract coupling:
 * - The canonical key set and numeric metadata is shared via `contracts/params.json`.
 * - The test `params.contract.test.ts` verifies `PARAMS` matches the contract 1:1
 *   for the contract-relevant fields.
 */

import type { ParamRegistry } from "../types/params";

export const PARAMS: ParamRegistry = {
  year: {
    key: "year",
    name: "Year",
    description: "Year for which the analysis will be performed",
    paramType: "static",
    editable: true,
    order: 100,
    valueType: "number",
    unit: "-",
    min: 1990,
    max: 2023,
    default: 2020,
  },

  thickness: {
    key: "thickness",
    name: "Thickness",
    description: "Vertical thickness of the aquifer storage layer",
    paramType: "static",
    editable: true,
    order: 110,
    valueType: "number",
    unit: "m",
    min: 10,
    max: 200,
    default: 30,
  },

  wellRadius: {
    key: "wellRadius",
    name: "Well radius",
    description: "Radius of the well bores",
    paramType: "static",
    editable: true,
    order: 111,
    valueType: "number",
    unit: "m",
    min: 0.05,
    max: 2,
    default: 0.2,
  },

  wellDistance: {
    key: "wellDistance",
    name: "Well distance",
    description: "Center-to-center distance between warm and cold wells in each well pair",
    paramType: "static",
    editable: true,
    order: 112,
    valueType: "number",
    unit: "m",
    min: 10,
    max: 1000,
    default: 100,
  },

  maxDrawdown: {
    key: "maxDrawdown",
    name: "Max drawdown",
    description: "Maximum allowable drawdown at each well boundary",
    paramType: "static",
    editable: true,
    order: 113,
    valueType: "number",
    unit: "m",
    min: 1,
    max: 20,
    default: 1.5,
  },

  fluidDensity: {
    key: "fluidDensity",
    name: "Fl. density",
    description: "Density of the fluid in the aquifer",
    paramType: "static",
    editable: true,
    order: 120,
    valueType: "number",
    unit: "kg/m³",
    min: 100,
    max: 2000,
    default: 1000,
  },

  fluidSpecHeatCap: {
    key: "fluidSpecHeatCap",
    name: "Fl. spec. heat cap.",
    description: "Specific heat capacity of the fluid stored in the aquifer",
    paramType: "static",
    editable: true,
    order: 121,
    valueType: "number",
    unit: "J/(kg·K)",
    min: 100,
    max: 10000,
    default: 4180,
  },

  porosity: {
    key: "porosity",
    name: "Porosity",
    description: "Aquifer porosity (fraction of pure volume)",
    paramType: "static",
    editable: true,
    order: 122,
    valueType: "number",
    unit: "-",
    min: 0.01,
    max: 0.5,
    default: 0.2,
  },

  tempDiff: {
    key: "tempDiff",
    name: "Temp. diff.",
    description: "Average temperature spread between warm wells and cold wells",
    paramType: "static",
    editable: true,
    order: 130,
    valueType: "number",
    unit: "K",
    min: 1,
    max: 20,
    default: 5,
  },

  rockType: {
    key: "rockType",
    name: "Rock type",
    description: "Type of solid material forming the aquifer",
    paramType: "local",
    editable: false,
    order: 200,
    valueType: "string",
  },

  rockDensity: {
    key: "rockDensity",
    name: "Rock density",
    description: "Density of the solid material forming the aquifer",
    paramType: "local",
    editable: true,
    order: 201,
    valueType: "number",
    unit: "kg/m³",
    min: 1000,
    max: 4000,
  },

  rockSpecHeatCap: {
    key: "rockSpecHeatCap",
    name: "Rock spec. heat cap.",
    description: "Specific heat capacity of the solid material forming the aquifer",
    paramType: "local",
    editable: true,
    order: 202,
    valueType: "number",
    unit: "J/(kg·K)",
    min: 500,
    max: 2000,
  },

  rockThermCond: {
    key: "rockThermCond",
    name: "Rock therm. cond.",
    description: "Thermal conductivity of the solid material forming the aquifer",
    paramType: "local",
    editable: true,
    order: 203,
    valueType: "number",
    unit: "W/(m·K)",
    min: 0.1,
    max: 10,
  },

  hydrCond: {
    key: "hydrCond",
    name: "Hydr. cond.",
    description: "Hydraulic conductivity of the aquifer",
    paramType: "local",
    editable: true,
    order: 210,
    valueType: "number",
    unit: "m/s",
    min: 1e-12,
    max: 1e-2,
    displayUnit: "m/d",
    displayScaleFactor: 86400,
  },

  hydrGrad: {
    key: "hydrGrad",
    name: "Hydr. grad.",
    description:
      "Absolute value of the hydraulic gradient in the aquifer, representing the change in hydraulic head per unit distance in the direction of the steepest descent of hydraulic head.",
    paramType: "local",
    editable: true,
    order: 211,
    valueType: "number",
    unit: "-",
    min: 0,
    max: 1,
  },

  heatPeriodStart: {
    key: "heatPeriodStart",
    name: "Heat. period start",
    description:
      "Starting day of the annual heating period (DD.MM). Periods can wrap around the year boundary. Heating and cooling periods must not overlap.",
    paramType: "local",
    editable: true,
    order: 230,
    valueType: "string",
  },

  heatPeriodEnd: {
    key: "heatPeriodEnd",
    name: "Heat. period end",
    description:
      "Ending day of the annual heating period (DD.MM). Periods can wrap around the year boundary. Heating and cooling periods must not overlap.",
    paramType: "local",
    editable: true,
    order: 231,
    valueType: "string",
  },

  coolPeriodStart: {
    key: "coolPeriodStart",
    name: "Cool. period start",
    description:
      "Starting day of the annual cooling period (DD.MM). Periods can wrap around the year boundary. Heating and cooling periods must not overlap.",
    paramType: "local",
    editable: true,
    order: 232,
    valueType: "string",
  },

  coolPeriodEnd: {
    key: "coolPeriodEnd",
    name: "Cool. period end",
    description:
      "Ending day of the annual cooling period (DD.MM). Periods can wrap around the year boundary. Heating and cooling periods must not overlap.",
    paramType: "local",
    editable: true,
    order: 233,
    valueType: "string",
  },
};
