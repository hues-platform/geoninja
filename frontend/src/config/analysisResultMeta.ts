/**
 * Analysis result metadata (frontend).
 *
 * The backend returns result items identified by stable `key` strings.
 * This file provides UI metadata for those keys:
 * - human-readable names/descriptions
 * - optional display units and display scaling
 * - optional ordering hints
 *
 * Contract coupling:
 * - The canonical set of result keys/units is defined in `contracts/analysis_results.json`.
 * - The test `analysisResultMeta.contract.test.ts` ensures this map stays in 1:1 sync
 *   with the contract (no missing or extra keys).
 */

export type AnalysisResultMeta = {
  key: string;
  name: string;
  description?: string | null;
  order?: number; // optional display ordering
  displayUnit?: string; // optional unit for display purposes
  displayScaleFactor?: number; // multiply value by this to reach display unit
};

export const ANALYSIS_RESULT_META: Record<string, AnalysisResultMeta> = {
  hydrTrans: {
    key: "hydrTrans",
    name: "Hydr. trans.",
    description:
      "Hydraulic Transmissivity of the Aquifer. Calculated as hydraulic conductivity multiplied by aquifer thickness.",
    displayUnit: "m²/d",
    displayScaleFactor: 86400,
  },

  darcyVelo: {
    key: "darcyVelo",
    name: "Darcy velo.",
    description:
      "Absolute value of the Darcy Velocity (specific discharge) of the aquifer. Calculated as hydraulic conductivity multiplied by hydraulic gradient.",
    displayUnit: "m/d",
    displayScaleFactor: 86400,
  },

  poreVelo: {
    key: "poreVelo",
    name: "Pore velo.",
    description:
      "Absolute value of the Pore Velocity of the aquifer. Calculated as Darcy velocity divided by porosity.",
    displayUnit: "m/d",
    displayScaleFactor: 86400,
  },

  thermFrontVelo: {
    key: "thermFrontVelo",
    name: "Therm. front velo.",
    description:
      "Absolute value of the Thermal Front Velocity in the aquifer. Calculated as pore velocity multiplied by the thermal retardation factor, which is calculated as porosity multiplied by the volumetric heat capacity of the fluid, divided by the volumetric heat capacity of the aquifer.",
    displayUnit: "m/d",
    displayScaleFactor: 86400,
  },

  retardFact: {
    key: "retardFact",
    name: "Retard. fact.",
    description:
      "Thermal retardation factor, calculated as porosity multiplied by the volumetric heat capacity of the fluid, divided by the volumetric heat capacity of the aquifer.",
  },

  fluidVolHeatCap: {
    key: "fluidVolHeatCap",
    name: "Fl. vol. heat cap.",
    description:
      "Volumetric Heat Capacity of the Fluid. Calculated as fluid density multiplied by fluid specific heat capacity.",
    displayUnit: "MJ/(m³·K)",
    displayScaleFactor: 1e-6,
  },

  rockVolHeatCap: {
    key: "rockVolHeatCap",
    name: "Rock vol. heat cap.",
    description:
      "Volumetric Heat Capacity of the Rock. Calculated as rock density multiplied by rock specific heat capacity.",
    displayUnit: "MJ/(m³·K)",
    displayScaleFactor: 1e-6,
  },

  aqVolHeatCap: {
    key: "aqVolHeatCap",
    name: "Aq. vol. heat cap.",
    description:
      "Volumetric Heat Capacity of the Aquifer. Calculated as a porosity-weighted average of the fluid and rock volumetric heat capacities.",
    displayUnit: "MJ/(m³·K)",
    displayScaleFactor: 1e-6,
  },

  storativity: {
    key: "storativity",
    name: "Storativity",
    description:
      "Storativity of the aquifer, representing the volume of water released from storage per unit surface area of the aquifer per unit decline in hydraulic head. Is currently approximated in GeoNinja by the porosity of the aquifer.",
    displayUnit: "-",
  },

  heatingDays: {
    key: "heatingDays",
    name: "Heating days",
    description: "Number of days the aquifer spends in heating mode.",
    displayUnit: "d",
  },

  coolingDays: {
    key: "coolingDays",
    name: "Cooling days",
    description: "Number of days the aquifer spends in cooling mode.",
    displayUnit: "d",
  },

  maxVolFlowRateHeat: {
    key: "maxVolFlowRateHeat",
    name: "Max. vol. flow rate (heat)",
    description:
      "Maximum sustainable volumetric flow rate during heating based on allowable effective drawdown at the boundary of the warm extraction well. This effective drawdown is modeled based on the superposition of the drawdown caused by the extraction at the warm well and the lift caused by the injection at the cold well. The physics of this procedure are modeled assuming an infinite, homogeneous, isotropic, confined aquifer, and we use the Theis equation to calculate the respective drawdown and lift.",
    displayUnit: "m³/h",
    displayScaleFactor: 3600,
  },

  maxVolFlowRateCool: {
    key: "maxVolFlowRateCool",
    name: "Max. vol. flow rate (cool)",
    description:
      "Maximum sustainable volumetric flow rate during cooling based on allowable effective drawdown at the boundary of the cold extraction well. This effective drawdown is modeled based on the superposition of the drawdown caused by the extraction at the cold well and the lift caused by the injection at the warm well. The physics of this procedure are modeled assuming an infinite, homogeneous, isotropic, confined aquifer, and we use the Theis equation to calculate the respective drawdown and lift.",
    displayUnit: "m³/h",
    displayScaleFactor: 3600,
  },

  maxMassFlowRateHeat: {
    key: "maxMassFlowRateHeat",
    name: "Max. mass flow rate (heat)",
    description:
      "Maximum sustainable mass flow rate during heating, calculated as the maximal volumetric flow rate during heating multiplied by the fluid density.",
    displayUnit: "kg/h",
    displayScaleFactor: 3600,
  },

  maxMassFlowRateCool: {
    key: "maxMassFlowRateCool",
    name: "Max. mass flow rate (cool)",
    description:
      "Maximum sustainable mass flow rate during cooling, calculated as the maximal volumetric flow rate during cooling multiplied by the fluid density.",
    displayUnit: "kg/h",
    displayScaleFactor: 3600,
  },

  maxHeatRate: {
    key: "maxHeatRate",
    name: "Max. heat rate",
    description:
      "Maximum sustainable heating rate. This rate is calculated as the product of maximum mass flow rate, the fluid's specific heat capacity and the temperature difference between wells.",
    displayUnit: "kW",
    displayScaleFactor: 1e-3,
  },

  maxCoolRate: {
    key: "maxCoolRate",
    name: "Max. cool rate",
    description:
      "Maximum sustainable cooling rate. This rate is calculated as the product of maximum mass flow rate, the fluid's specific heat capacity and the temperature difference between wells.",
    displayUnit: "kW",
    displayScaleFactor: 1e-3,
  },

  thermRadVolEqWarmWell: {
    key: "thermRadVolEqWarmWell",
    name: "Therm. rad. (vol-eq) warm well",
    description:
      "Volumetric-equivalent thermal radius of the warm well. Defined as the radius of a theoretical cylindrical volume in the aquifer (with height equal to the aquifer thickness) that contains the same total thermal energy as the fluid volume injected into the warm well during the cooling period. Based on Doughty et al: 'A dimensionless parameter approach to the thermal behavior of an aquifer thermal energy storage system', 1982.",
  },

  thermRadVolEqColdWell: {
    key: "thermRadVolEqColdWell",
    name: "Therm. rad. (vol-eq) cold well",
    description:
      "Volumetric-equivalent thermal radius of the cold well. Defined as the radius of a theoretical cylindrical volume in the aquifer (with height equal to the aquifer thickness) that contains the same total thermal energy as the fluid volume injected into the cold well during the heating period. Based on Doughty et al: 'A dimensionless parameter approach to the thermal behavior of an aquifer thermal energy storage system', 1982.",
  },

  thermRadAdvWarmWell: {
    key: "thermRadAdvWarmWell",
    name: "Therm. rad. (adv) warm well",
    description:
      "Advective thermal radius of the warm well. Defined as the distance that the thermal front migrates in the aquifer during the cooling period, based on the thermal front velocity.",
  },

  thermRadAdvColdWell: {
    key: "thermRadAdvColdWell",
    name: "Therm. rad. (adv) cold well",
    description:
      "Advective thermal radius of the cold well. Defined as the distance that the thermal front migrates in the aquifer during the heating period, based on the thermal front velocity.",
  },

  thermRadWarmWell: {
    key: "thermRadWarmWell",
    name: "Therm. rad. warm well",
    description:
      "Overall thermal radius of the warm well. Calculated as the sum of the volumetric-equivalent thermal radius and the advective thermal radius of the warm well.",
  },

  thermRadColdWell: {
    key: "thermRadColdWell",
    name: "Therm. rad. cold well",
    description:
      "Overall thermal radius of the cold well. Calculated as the sum of the volumetric-equivalent thermal radius and the advective thermal radius of the cold well.",
  },

  thermArea: {
    key: "thermArea",
    name: "Therm. area",
    description:
      "Surface-projected area of the thermally relevant area of a well doublet system. Calculated as the smallest rectangle that encloses the circles defined by the thermal radii of the warm and cold wells.",
  },

  maxHeatDensity: {
    key: "maxHeatDensity",
    name: "Max. heat density",
    description:
      "Maximum sustainable heating rate per unit area of the thermally relevant area of the well doublet system. Calculated as the maximum heating rate divided by the thermal area.",
  },

  maxCoolDensity: {
    key: "maxCoolDensity",
    name: "Max. cool density",
    description:
      "Maximum sustainable cooling rate per unit area of the thermally relevant area of the well doublet system. Calculated as the maximum cooling rate divided by the thermal area.",
  },
};
